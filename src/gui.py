import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
from backend import DNSBackend
import config
import lang
import threading
import os

# --- Persian Text Support ---
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    HAS_SHAPING = True
except ImportError:
    # This error is expected if the packages are not installed (as shown in the user's log)
    HAS_SHAPING = False


class ConfigDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent.master_app
        self.title(self.parent_app.t("settings_title"))
        self.geometry("550x700")
        self.transient(parent)
        self.resizable(False, False)

        self.main_font = self.parent_app.default_font
        l = config.get_setting("language")

        def t(k): return self.parent_app.fix_text(lang.get_text(l, k))

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Language ---
        tk.Label(main_frame, text="Language / زبان:", font=self.main_font).pack(anchor=tk.W, pady=(10, 2))
        self.lang_var = tk.StringVar(value=l)
        ttk.Combobox(main_frame, textvariable=self.lang_var, values=["EN", "FA", "ZH", "RU"], state="readonly").pack(
            fill=tk.X)

        # --- Update URLs (Dynamic Fields) ---
        tk.Label(main_frame, text=t("lbl_urls"), font=self.main_font).pack(anchor=tk.W, pady=(15, 2))

        url_container = ttk.Frame(main_frame)
        url_container.pack(fill=tk.X)

        self.url_entries_frame = tk.Frame(url_container, height=200, bd=1, relief="sunken")
        self.url_entries_frame.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(self.url_entries_frame, borderwidth=0, background="#ffffff")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_y = ttk.Scrollbar(self.url_entries_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.inner_frame = ttk.Frame(self.canvas)
        # 500 is roughly the width of the dialog minus padding/scrollbar
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", width=500)
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.url_entries = []
        current_urls = config.get_setting("update_urls")
        for url in current_urls:
            self._add_url_entry(url)

        ttk.Button(main_frame, text=self.parent_app.fix_text("+ Add Link"), command=lambda: self._add_url_entry()).pack(
            pady=(5, 10), anchor=tk.W)

        # --- Domain ---
        tk.Label(main_frame, text=t("lbl_domain"), font=self.main_font).pack(anchor=tk.W, pady=(15, 2))
        self.ent_domain = ttk.Entry(main_frame)
        self.ent_domain.pack(fill=tk.X)
        self.ent_domain.insert(0, config.get_setting("test_domain"))

        # --- Auto Clean Rules ---
        tk.Label(main_frame, text=t("lbl_limits"), font=(self.main_font[0], 11, "bold")).pack(anchor=tk.W, pady=(20, 5))

        self.var_auto_clean = tk.BooleanVar(value=config.get_setting("auto_clean_enabled"))
        chk = tk.Checkbutton(main_frame, text=t("chk_auto_clean"), variable=self.var_auto_clean, font=self.main_font)
        chk.pack(anchor=tk.W, padx=5)

        f_limits = tk.Frame(main_frame)
        f_limits.pack(fill=tk.X, pady=5)

        tk.Label(f_limits, text=t("lbl_max_ping"), font=self.main_font).pack(side=tk.LEFT)
        self.ent_ping = ttk.Entry(f_limits, width=8)
        self.ent_ping.pack(side=tk.LEFT, padx=(5, 15))
        self.ent_ping.insert(0, config.get_setting("ping_limit"))

        tk.Label(f_limits, text=t("lbl_max_speed"), font=self.main_font).pack(side=tk.LEFT)
        self.ent_speed = ttk.Entry(f_limits, width=8)
        self.ent_speed.pack(side=tk.LEFT, padx=5)
        self.ent_speed.insert(0, config.get_setting("speed_limit"))

        ttk.Button(main_frame, text=self.parent_app.fix_text("Save & Restart"), command=self.save_settings).pack(
            pady=20)

    def _add_url_entry(self, url=""):
        f = ttk.Frame(self.inner_frame)
        f.pack(fill=tk.X, pady=2, padx=5)

        entry = ttk.Entry(f)
        entry.insert(0, url)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipadx=2)

        btn_remove = ttk.Button(f, text="x", width=3, command=lambda: self._remove_url_entry(f))
        btn_remove.pack(side=tk.RIGHT, padx=(5, 0))

        self.url_entries.append({'frame': f, 'entry': entry})
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _remove_url_entry(self, frame_to_remove):
        self.url_entries = [item for item in self.url_entries if item['frame'] != frame_to_remove]
        frame_to_remove.destroy()
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def save_settings(self):
        new_urls = [item['entry'].get().strip() for item in self.url_entries if item['entry'].get().strip()]

        try:
            p_limit = int(self.ent_ping.get().strip())
        except:
            p_limit = 400
        try:
            s_limit = int(self.ent_speed.get().strip())
        except:
            s_limit = 300

        config.save_config("update_urls", new_urls)
        config.save_config("test_domain", self.ent_domain.get().strip())
        config.save_config("ping_limit", p_limit)
        config.save_config("speed_limit", s_limit)
        config.save_config("auto_clean_enabled", self.var_auto_clean.get())

        new_lang = self.lang_var.get()
        if new_lang != config.get_setting("language"):
            config.save_config("language", new_lang)
            messagebox.showinfo("Restart", "Please restart application.")

        self.destroy()


class DNSApp:
    def __init__(self, root):
        self.root = root
        self.root.master_app = self
        self.backend = DNSBackend()
        self.root.geometry("950x750")

        self.current_lang = config.get_setting("language") or "EN"

        # --- Font Configuration for Persian ---
        # Prioritize Noto Sans (or fallback to a common font like Tahoma if Noto is missing)
        font_name = "Noto Sans"
        if not font.families().count(font_name):
            font_name = "Tahoma" if font.families().count("Tahoma") else "TkDefaultFont"

        self.default_font = (font_name, 10)

        style = ttk.Style()
        style.configure(".", font=self.default_font)
        style.configure("Treeview", font=self.default_font, rowheight=25)
        style.configure("Treeview.Heading", font=(self.default_font[0], 10, "bold"))

        self.root.option_add("*Font", self.default_font)

        if os.geteuid() != 0:
            messagebox.showwarning("Sudo", self.t("err_perm"))

        self.setup_ui()
        self.refresh_dns_list()

    def t(self, key):
        """Translate and reshape."""
        text = lang.get_text(self.current_lang, key)
        return self.fix_text(text)

    def fix_text(self, text):
        """
        Fix Persian letters being disjointed.
        """
        if self.current_lang == "FA" and HAS_SHAPING:
            try:
                reshaped = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped)
                return bidi_text
            except Exception:
                return text
        return text

    # FIXED: This method was present but may have been incorrectly indented or referenced
    def update_conn_info(self):
        """Gets and displays active network connection info."""
        conn = self.backend.get_active_connection()
        if conn:
            self.lbl_conn.config(text=self.t("conn_active").format(conn), fg="green")
            return conn
        self.lbl_conn.config(text=self.t("conn_none"), fg="red")
        return None

    def setup_ui(self):
        self.root.title(self.t("app_title"))

        # Header
        top_frame = tk.Frame(self.root, bg="#34495e", height=60)
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text=self.t("header"), bg="#34495e", fg="white",
                 font=(self.default_font[0], 16, "bold")).pack(pady=15)

        tk.Button(top_frame, text="⚙", command=lambda: ConfigDialog(self.root), bg="#2c3e50", fg="white", bd=0).place(
            relx=0.94, rely=0.3)

        # Network Status
        conn_frame = tk.Frame(self.root, pady=5, padx=10)
        conn_frame.pack(fill=tk.X)
        self.lbl_conn = tk.Label(conn_frame, text=self.t("scan"))
        self.lbl_conn.pack(side=tk.LEFT)
        # The reference is now correct: self.update_conn_info
        tk.Button(conn_frame, text=self.t("refresh"), command=self.update_conn_info).pack(side=tk.RIGHT)

        # Treeview
        tree_frame = tk.Frame(self.root, padx=10, pady=5)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('name', 'ipv4', 'ping', 'speed')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='extended')

        self.tree.heading('name', text=self.t("col_name"), command=lambda: self.sort_tree('name', False))
        self.tree.heading('ipv4', text=self.t("col_ipv4"), command=lambda: self.sort_tree('ipv4', False))
        self.tree.heading('ping', text=self.t("col_ping"), command=lambda: self.sort_tree('ping', False))
        self.tree.heading('speed', text=self.t("col_speed"), command=lambda: self.sort_tree('speed', False))

        self.tree.column('name', width=250)
        self.tree.column('ipv4', width=250)
        self.tree.column('ping', width=80, anchor=tk.CENTER)
        self.tree.column('speed', width=80, anchor=tk.CENTER)

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Controls
        ctrl_frame = tk.LabelFrame(self.root, text=self.t("menu_settings"), padx=10, pady=10)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=10)

        # Row 1
        r1 = tk.Frame(ctrl_frame)
        r1.pack(fill=tk.X, pady=5)
        ttk.Button(r1, text=self.t("btn_apply"), command=self.apply_dns).pack(side=tk.LEFT, padx=5)

        tk.Label(r1, text=self.t("test_mode")).pack(side=tk.LEFT, padx=(20, 5))
        self.test_var = tk.StringVar(value="all")
        ttk.OptionMenu(r1, self.test_var, "all", "all", "ping", "dig").pack(side=tk.LEFT)

        ttk.Button(r1, text=self.t("btn_test"), command=self.run_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(r1, text=self.t("btn_update"), command=self.update_list).pack(side=tk.RIGHT, padx=5)

        # Row 2
        r2 = tk.Frame(ctrl_frame)
        r2.pack(fill=tk.X, pady=5)
        tk.Button(r2, text=self.t("btn_del"), command=self.delete_selected, bg="#e74c3c", fg="white").pack(side=tk.LEFT,
                                                                                                           padx=5)

        mb = tk.Menubutton(r2, text=self.t("btn_cond_del"), bg="#c0392b", fg="white", relief=tk.RAISED)
        mb.menu = tk.Menu(mb, tearoff=0)
        mb["menu"] = mb.menu
        mb.menu.add_command(label=self.t("opt_clean_settings"), command=self.clean_dead)
        mb.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, bg="#ecf0f1").pack(
            side=tk.BOTTOM, fill=tk.X)

        self.update_conn_info()  # Initial call

    def refresh_dns_list(self):
        self.tree.delete(*self.tree.get_children())

        def_name = "Default (System/DHCP)"
        if self.current_lang == "FA": def_name = self.fix_text("پیش‌فرض (سیستم)")
        self.tree.insert('', tk.END, values=(def_name, "Automatic", '-', '-'), tags=('default',))

        self.dns_data = self.backend.load_dns_list()
        for name, d in self.dns_data.items():
            all_ips = d.get("ipv4", []) + d.get("ipv6", [])
            ipv_display = ", ".join(all_ips)

            dn = self.fix_text(name) if self.current_lang == "FA" else name
            self.tree.insert('', tk.END, values=(dn, ipv_display, d.get('last_ping', '-'), d.get('last_speed', '-')))

        self.tree.tag_configure('default', background='#dff9fb')

    def apply_dns(self):
        sel = self.tree.selection()
        if not sel: return
        conn = self.update_conn_info()
        if not conn: return

        vals = self.tree.item(sel[0])['values']
        name_display = vals[0]

        if "Default" in str(name_display) or "پیش‌فرض" in str(name_display):
            self.backend.clear_dns(conn)
            messagebox.showinfo(self.t("app_title"), self.fix_text("تنظیمات به DHCP بازنشانی شد."))
            return

        target_key = None
        for k in self.dns_data.keys():
            if self.fix_text(k) == name_display or k == name_display:
                target_key = k
                break

        if target_key:
            d = self.dns_data[target_key]
            ok, msg = self.backend.set_dns(conn, d.get("ipv4", []), d.get("ipv6", []))
            if ok:
                messagebox.showinfo(self.t("app_title"), self.t("msg_apply"))
            else:
                messagebox.showerror(self.t("app_title"), msg)

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno(self.t("app_title"), self.t("confirm_del")):
            count = 0
            for item_id in sel:
                vals = self.tree.item(item_id)['values']
                name = vals[0]
                if "Default" in name or "پیش‌فرض" in name: continue

                for k in list(self.dns_data.keys()):
                    if self.fix_text(k) == name or k == name:
                        del self.dns_data[k]
                        count += 1
                        break
            self.backend.save_dns_list(self.dns_data)
            self.refresh_dns_list()
            self.status_var.set(self.t("msg_del").format(count))

    def clean_dead(self):
        if messagebox.askyesno(self.t("app_title"), self.fix_text(
                "آیا می‌خواهید تمامی سرورهایی که قوانین تنظیمات را نقض کرده‌اند، حذف کنید؟")):
            deleted = self.perform_batch_cleaning()
            self.status_var.set(self.t("msg_clean").format(deleted))

    def perform_batch_cleaning(self):
        p_limit = config.get_setting("ping_limit")
        s_limit = config.get_setting("speed_limit")

        to_del = []
        for k, v in self.dns_data.items():
            p = str(v.get('last_ping', '-'))
            s = str(v.get('last_speed', '-'))

            should_del = False
            # Rule 1: Dead (9999)
            if p == '9999' or s == '9999': should_del = True
            # Rule 2: Limits
            if p.isdigit() and int(p) > p_limit: should_del = True
            if s.isdigit() and int(s) > s_limit: should_del = True

            if should_del: to_del.append(k)

        for k in to_del:
            if k in self.dns_data: del self.dns_data[k]

        self.backend.save_dns_list(self.dns_data)
        self.refresh_dns_list()
        return len(to_del)

    def update_list(self):
        urls = config.get_setting("update_urls")
        if not urls:
            messagebox.showwarning(self.t("app_title"),
                                   self.fix_text("لطفاً ابتدا لینک‌های آپدیت را در تنظیمات وارد کنید."))
            return

        self.status_var.set(self.t("msg_wait"))
        self.root.update()

        def import_worker():
            try:
                c = self.backend.import_from_urls(urls)
                self.root.after(0, lambda count=c: self._after_update_list(count))
            except Exception as e:
                self.root.after(0,
                                lambda: messagebox.showerror(self.t("app_title"), self.fix_text(f"Import failed: {e}")))
                self.root.after(0, lambda: self.status_var.set(self.t("status_ready")))

        threading.Thread(target=import_worker, daemon=True).start()

    def _after_update_list(self, count):
        self.refresh_dns_list()
        messagebox.showinfo(self.t("app_title"), self.fix_text(f"تعداد {count} ورودی جدید اضافه شد."))
        self.status_var.set(self.t("status_ready"))

    def run_test(self):
        self.status_var.set(self.t("msg_wait"))
        threading.Thread(target=self._test_worker, daemon=True).start()

    def _test_worker(self):
        items = list(self.tree.get_children())
        mode = self.test_var.get()
        domain = config.get_setting("test_domain")

        auto_clean = config.get_setting("auto_clean_enabled")
        ping_limit = config.get_setting("ping_limit")
        speed_limit = config.get_setting("speed_limit")

        total_items = len(items)
        items_processed = 0

        for item in items:
            if item not in self.tree.get_children(): continue

            items_processed += 1
            self.root.after(0, lambda idx=items_processed: self.status_var.set(
                self.t("status_testing").format(idx, total_items)))

            try:
                vals = self.tree.item(item)['values']
            except:
                continue

            name_display = vals[0]
            if "Default" in name_display or "پیش‌فرض" in name_display: continue

            key = None
            for k in list(self.dns_data.keys()):
                if self.fix_text(k) == name_display or k == name_display:
                    key = k
                    break

            if not key or key not in self.dns_data: continue

            target_ip_list = self.dns_data[key].get('ipv4', []) + self.dns_data[key].get('ipv6', [])
            if not target_ip_list: continue
            target_ip = target_ip_list[0]

            ping, speed = vals[2], vals[3]

            # --- PING TEST ---
            if mode in ["all", "ping"]:
                new_ping = self.backend.measure_ping(target_ip)

                if auto_clean:
                    is_dead = new_ping == 9999
                    is_slow = new_ping != 9999 and new_ping > ping_limit
                    if is_dead or is_slow:
                        self.root.after(0, self._delete_row_safe, item, key)
                        continue

                ping = new_ping
                self.dns_data[key]['last_ping'] = ping

            # --- DIG TEST ---
            if mode in ["all", "dig"]:
                new_speed = self.backend.measure_dig_speed(target_ip, domain)

                if auto_clean:
                    is_dead = new_speed == 9999
                    is_slow = new_speed != 9999 and new_speed > speed_limit
                    if is_dead or is_slow:
                        self.root.after(0, self._delete_row_safe, item, key)
                        continue

                speed = new_speed
                self.dns_data[key]['last_speed'] = speed

            self.root.after(0, self._update_row, item, ping, speed)

        self.backend.save_dns_list(self.dns_data)
        self.root.after(0, lambda: self.status_var.set(self.t("status_ready")))

    def _delete_row_safe(self, item, key):
        """Thread-safe deletion for fail-fast logic"""
        try:
            if item in self.tree.get_children():
                self.tree.delete(item)
            if key in self.dns_data:
                del self.dns_data[key]
            self.backend.save_dns_list(self.dns_data)
        except:
            pass

    def _update_row(self, item, ping, speed):
        try:
            vals = self.tree.item(item)['values']
            self.tree.item(item, values=(vals[0], vals[1], ping, speed))
        except:
            pass

    def sort_tree(self, col, reverse):
        l = []
        for k in self.tree.get_children(''):
            value = self.tree.set(k, col)
            l.append((value, k))

        if col in ('ping', 'speed'):
            # Numerical sort: Treat non-digits (like '-', '9999') as a very high number (99999)
            def sort_key(t):
                v = str(t[0]).strip()
                try:
                    return float(v)
                except ValueError:
                    return 99999.0
        else:  # 'name', 'ipv4' (string sort)
            def sort_key(t):
                return str(t[0]).lower()

        l.sort(key=sort_key, reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_tree(col, not reverse))