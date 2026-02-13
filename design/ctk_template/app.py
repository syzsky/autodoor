import customtkinter as ctk
from theme import Theme, init_theme


class NumericEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._valid = True
        
        self.bind('<KeyRelease>', self._validate)
        self.bind('<FocusOut>', self._validate)
    
    def _validate(self, event=None):
        value = self.get()
        if value == '' or value == '-':
            self._valid = True
            self.configure(border_color=Theme.COLORS['border'])
            return
        
        try:
            float(value)
            self._valid = True
            self.configure(border_color=Theme.COLORS['success'])
        except ValueError:
            self._valid = False
            self.configure(border_color=Theme.COLORS['error'])
    
    def is_valid(self):
        return self._valid
    
    def get_value(self, default=0):
        try:
            return float(self.get())
        except ValueError:
            return default


class CardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault('corner_radius', 8)
        kwargs.setdefault('border_width', 1)
        kwargs.setdefault('border_color', '#E5E7EB')
        super().__init__(master, **kwargs)
        
        self._default_bg = kwargs.get('fg_color', '#ffffff')
        self._hover_bg = '#F9FAFB'
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        pass
    
    def _on_leave(self, event):
        pass


class AnimatedButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        self._press_color = kwargs.pop('press_color', None)
        self._original_fg = kwargs.get('fg_color', Theme.COLORS['primary'])
        self._original_hover = kwargs.get('hover_color', Theme.COLORS['primary_hover'])
        
        if self._press_color is None:
            if isinstance(self._original_fg, str):
                self._press_color = self._darken_color(self._original_fg, 0.2)
            else:
                self._press_color = self._original_hover
        
        super().__init__(master, **kwargs)
        
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
    
    def _darken_color(self, hex_color, factor):
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color
    
    def _on_press(self, event):
        self.configure(fg_color=self._press_color)
    
    def _on_release(self, event):
        self.configure(fg_color=self._original_fg)


class LoadingOverlay:
    def __init__(self, parent, message='加载中...'):
        self.parent = parent
        self.message = message
        self.overlay = None
        self.is_showing = False
    
    def show(self):
        if self.is_showing:
            return
        
        self.overlay = ctk.CTkFrame(self.parent, fg_color='rgba(0,0,0,0.5)')
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        content = ctk.CTkFrame(self.overlay, corner_radius=12)
        content.place(relx=0.5, rely=0.5, anchor='center')
        
        spinner_frame = ctk.CTkFrame(content, fg_color='transparent')
        spinner_frame.pack(padx=20, pady=(20, 10))
        
        self.spinner_label = ctk.CTkLabel(spinner_frame, text='◐', font=('Arial', 32), text_color=Theme.COLORS['primary'])
        self.spinner_label.pack()
        
        self._animate_spinner()
        
        ctk.CTkLabel(content, text=self.message, font=Theme.get_font('sm')).pack(padx=20, pady=(0, 20))
        
        self.is_showing = True
    
    def _animate_spinner(self):
        if not self.is_showing:
            return
        
        current = self.spinner_label.cget('text')
        chars = ['◐', '◓', '◑', '◒']
        idx = chars.index(current) if current in chars else 0
        next_idx = (idx + 1) % len(chars)
        self.spinner_label.configure(text=chars[next_idx])
        
        if self.is_showing:
            self.spinner_label.after(100, self._animate_spinner)
    
    def hide(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        self.is_showing = False
    
    def update_message(self, message):
        self.message = message


class AppTemplate:
    def __init__(self, title='AutoDoor OCR', version='2.0.4'):
        self._title = title
        self._version = version
        self._current_page = 'home'
        self._key_capture_callback = None
        self._key_capture_window = None
        self._loading_overlay = None
        
        init_theme()
        
        self._init_root()
        self._create_layout()
        self._create_pages()
    
    def _init_root(self):
        self.root = ctk.CTk()
        self.root.title(f'{self._title} v{self._version}')
        self.root.geometry('1050x700')
        self.root.minsize(950, 600)
        
        if Theme.SYSTEM == 'Windows':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
    
    def _create_layout(self):
        self._create_header()
        self._create_main_container()
        self._create_sidebar()
        self._create_content_area()
        self._create_footer()
    
    def _create_header(self):
        self.header = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        self.header.pack(fill='x')
        self.header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(self.header, fg_color='transparent')
        header_content.pack(fill='x', padx=12, pady=6)
        
        left_section = ctk.CTkFrame(header_content, fg_color='transparent')
        left_section.pack(side='left')
        
        ctk.CTkLabel(left_section, text='◉', font=Theme.get_font('xl'), text_color=Theme.COLORS['primary']).pack(side='left', padx=(0, 6))
        ctk.CTkLabel(left_section, text=self._title, font=Theme.get_font('lg')).pack(side='left')
        ctk.CTkLabel(left_section, text=f'v{self._version}', font=Theme.get_font('xs'), text_color=Theme.COLORS['primary'],
                     fg_color=Theme.COLORS['info_light'], corner_radius=4, padx=6, pady=1).pack(side='left', padx=8)
        
        center_section = ctk.CTkFrame(header_content, fg_color='transparent')
        center_section.pack(side='left', expand=True)
        
        self.status_frame = ctk.CTkFrame(center_section, fg_color='transparent')
        self.status_frame.pack()
        ctk.CTkLabel(self.status_frame, text='●', font=('Arial', 10), text_color=Theme.COLORS['success']).pack(side='left', padx=(0, 4))
        self.status_label = ctk.CTkLabel(self.status_frame, text='就绪', font=Theme.get_font('sm'), text_color=Theme.COLORS['success'])
        self.status_label.pack(side='left')
        
        right_section = ctk.CTkFrame(header_content, fg_color='transparent')
        right_section.pack(side='right')
        
        self._create_header_button(right_section, '检查更新', 
                                   command=lambda: self._show_loading_and_execute('检查更新', self._check_update))
        self._create_header_button(right_section, '工具介绍',
                                   command=lambda: self._show_notification('工具介绍', 'AutoDoor OCR - 自动化识别工具', 'info'))
        
        theme_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        theme_frame.pack(side='left', padx=8)
        ctk.CTkLabel(theme_frame, text='夜间模式', font=Theme.get_font('xs'), text_color=Theme.COLORS['text_secondary']).pack(side='left', padx=(0, 2))
        self.theme_switch = ctk.CTkSwitch(theme_frame, text='', width=36, command=self._toggle_theme)
        self.theme_switch.pack(side='left')
    
    def _create_header_button(self, parent, text, command):
        btn = ctk.CTkButton(parent, text=text, width=70, height=26, font=Theme.get_font('xs'),
                           fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                           corner_radius=6, border_width=0, command=command)
        btn.pack(side='left', padx=4)
        
        btn.bind('<Enter>', lambda e: btn.configure(cursor='hand2'))
        btn.bind('<Leave>', lambda e: btn.configure(cursor=''))
        
        return btn
    
    def _create_main_container(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color='transparent')
        self.main_container.pack(fill='both', expand=True)
    
    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.main_container, width=170, corner_radius=0)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        self.nav_items = {}
        nav_config = [('home', '🏠', '首页'), ('ocr', '📝', '文字识别'), ('timed', '⏱', '定时功能'),
                      ('number', '🔢', '数字识别'), ('script', '📜', '脚本运行'), ('settings', '⚙', '基本设置')]
        
        for i, (page_id, icon, text) in enumerate(nav_config):
            item = self._create_nav_item(self.sidebar, text, icon, lambda p=page_id: self._navigate_to(p), i == 0)
            item.pack(fill='x')
            self.nav_items[page_id] = item
    
    def _create_nav_item(self, master, text, icon, command, is_active):
        frame = ctk.CTkFrame(master, fg_color='transparent', corner_radius=0)
        indicator = ctk.CTkFrame(frame, width=3, height=22, fg_color='transparent', corner_radius=0)
        indicator.pack(side='left', padx=(6, 0), pady=6)
        
        content = ctk.CTkFrame(frame, fg_color='transparent')
        content.pack(side='left', fill='x', expand=True, padx=6, pady=6)
        
        icon_label = ctk.CTkLabel(content, text=icon, font=('Segoe UI Emoji', 14), width=24, anchor='center')
        icon_label.pack(side='left')
        
        text_label = ctk.CTkLabel(content, text=text, font=Theme.get_font('sm'), text_color=Theme.COLORS['text_secondary'], anchor='w')
        text_label.pack(side='left', padx=(4, 0))
        
        def on_enter(e):
            if not frame._is_active:
                frame.configure(fg_color=Theme.COLORS['info_light'])
        def on_leave(e):
            if not frame._is_active:
                frame.configure(fg_color='transparent')
        def on_click(e):
            command()
        
        frame._is_active = is_active
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        frame.bind('<Button-1>', on_click)
        icon_label.bind('<Button-1>', on_click)
        text_label.bind('<Button-1>', on_click)
        
        if is_active:
            frame.configure(fg_color=Theme.COLORS['info_light'])
            indicator.configure(fg_color=Theme.COLORS['primary'])
            text_label.configure(text_color=Theme.COLORS['primary'])
        
        frame._indicator = indicator
        frame._text_label = text_label
        return frame
    
    def _set_nav_active(self, page_id):
        for pid, item in self.nav_items.items():
            if pid == page_id:
                item._is_active = True
                item.configure(fg_color=Theme.COLORS['info_light'])
                item._indicator.configure(fg_color=Theme.COLORS['primary'])
                item._text_label.configure(text_color=Theme.COLORS['primary'])
            else:
                item._is_active = False
                item.configure(fg_color='transparent')
                item._indicator.configure(fg_color='transparent')
                item._text_label.configure(text_color=Theme.COLORS['text_secondary'])
    
    def _create_content_area(self):
        self.content_area = ctk.CTkFrame(self.main_container, fg_color='transparent')
        self.content_area.pack(side='left', fill='both', expand=True, padx=12, pady=12)
        self.pages = {}
    
    def _create_footer(self):
        self.footer = ctk.CTkFrame(self.root, height=28, corner_radius=0)
        self.footer.pack(fill='x')
        self.footer.pack_propagate(False)
        
        footer_content = ctk.CTkFrame(self.footer, fg_color='transparent')
        footer_content.pack(fill='x', padx=12, pady=4)
        
        ctk.CTkLabel(footer_content, text=f'{self._title} v{self._version} | 本程序仅供个人学习研究使用，禁止商用 | 制作人: ',
                    font=Theme.get_font('xs'), text_color=Theme.COLORS['text_muted']).pack(side='left')
        ctk.CTkLabel(footer_content, text='Flown王砖家', font=Theme.get_font('xs'), text_color=Theme.COLORS['primary']).pack(side='left')
    
    def _create_pages(self):
        self._create_home_page()
        self._create_ocr_page()
        self._create_timed_page()
        self._create_number_page()
        self._create_script_page()
        self._create_settings_page()
        self._show_page('home')
    
    def _create_section_title(self, parent, text, level=1):
        if level == 1:
            font = Theme.get_font('lg')
            text_color = Theme.COLORS['text_primary']
        elif level == 2:
            font = Theme.get_font('base')
            text_color = Theme.COLORS['text_primary']
        else:
            font = Theme.get_font('sm')
            text_color = Theme.COLORS['text_secondary']
        
        return ctk.CTkLabel(parent, text=text, font=font, text_color=text_color)
    
    def _create_divider(self, parent, orientation='horizontal'):
        if orientation == 'horizontal':
            divider = ctk.CTkFrame(parent, height=1, fg_color='#E5E7EB')
            divider.pack(fill='x', pady=8)
        else:
            divider = ctk.CTkFrame(parent, width=1, fg_color='#E5E7EB')
            divider.pack(fill='y', padx=8)
        return divider
    
    def _create_home_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.pages['home'] = page
        
        status_card = CardFrame(page, border_width=1, border_color='#E5E7EB')
        status_card.pack(fill='x', pady=(0, 12))
        
        status_header = ctk.CTkFrame(status_card, fg_color='transparent')
        status_header.pack(fill='x', padx=12, pady=(10, 6))
        self._create_section_title(status_header, '功能状态', level=1).pack(side='left')
        
        btn_row_header = ctk.CTkFrame(status_header, fg_color='transparent')
        btn_row_header.pack(side='right')
        
        self.start_btn = AnimatedButton(btn_row_header, text='▶ 开始运行', font=Theme.get_font('xs'), width=80, height=28,
                                        corner_radius=6, fg_color=Theme.COLORS['success'], 
                                        hover_color='#16A34A', press_color='#15803D',
                                        command=lambda: self._start_all_modules())
        self.start_btn.pack(side='left', padx=(0, 6))
        
        self.stop_btn = AnimatedButton(btn_row_header, text='⏹ 停止运行', font=Theme.get_font('xs'), width=80, height=28,
                                       fg_color=Theme.COLORS['error'], hover_color='#DC2626', press_color='#B91C1C',
                                       corner_radius=6, command=lambda: self._stop_all_modules())
        self.stop_btn.pack(side='left')
        
        self._create_divider(status_card)
        
        self.module_switches = {}
        self.module_indicators = {}
        modules = [('ocr', '文字识别'), ('timed', '定时功能'), ('number', '数字识别'), ('script', '脚本运行')]
        
        for key, name in modules:
            row = ctk.CTkFrame(status_card, fg_color='transparent')
            row.pack(fill='x', padx=12, pady=4)
            
            self._create_section_title(row, name, level=2).pack(side='left')
            
            indicator = ctk.CTkLabel(row, text='●', font=('Arial', 12), text_color='#9CA3AF')
            indicator.pack(side='left', padx=(8, 0))
            self.module_indicators[key] = indicator
            
            switch = ctk.CTkSwitch(row, text='', width=36)
            switch.pack(side='right')
            self.module_switches[key] = switch
        
        ctk.CTkFrame(status_card, height=8, fg_color='transparent').pack()
        
        log_card = CardFrame(page, border_width=1, border_color='#E5E7EB')
        log_card.pack(fill='both', expand=True)
        
        log_header = ctk.CTkFrame(log_card, fg_color='transparent')
        log_header.pack(fill='x', padx=12, pady=(10, 6))
        self._create_section_title(log_header, '运行日志', level=1).pack(side='left')
        
        self.log_text = ctk.CTkTextbox(log_card, font=('Consolas', 10), height=150)
        self.log_text.pack(fill='both', expand=True, padx=12, pady=(0, 8))
        self.log_text.insert('1.0', '[2024-01-15 10:30:00] 程序启动\n[2024-01-15 10:30:01] 系统初始化完成\n')
        
        clear_btn = AnimatedButton(log_card, text='清除日志', font=Theme.get_font('xs'), width=70, 
                                   fg_color='transparent', text_color=Theme.COLORS['primary'],
                                   hover_color=Theme.COLORS['info_light'], border_width=1, corner_radius=4,
                                   command=lambda: self.log_text.delete('1.0', 'end'))
        clear_btn.pack(side='right', padx=12, pady=(0, 10))
    
    def _create_key_input_with_button(self, parent, default_value, width=50):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.pack(side='left')
        
        entry = ctk.CTkEntry(frame, width=width, height=24, state='disabled')
        entry._original_state = 'disabled'
        entry.insert(0, default_value)
        entry.pack(side='left', padx=(2, 2))
        
        btn = AnimatedButton(frame, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                            fg_color=Theme.COLORS['text_muted'], hover_color=Theme.COLORS['text_secondary'],
                            press_color='#6B7280')
        btn.pack(side='left')
        
        btn._entry = entry
        btn.configure(command=lambda: self._start_key_capture(btn._entry))
        
        return entry
    
    def _create_numeric_entry(self, parent, default_value='', width=40, **kwargs):
        entry = NumericEntry(parent, width=width, height=24, **kwargs)
        if default_value:
            entry.insert(0, str(default_value))
        return entry
    
    def _start_key_capture(self, entry):
        capture_window = ctk.CTkToplevel(self.root)
        capture_window.title('按键捕获')
        capture_window.geometry('300x120')
        capture_window.attributes('-topmost', True)
        capture_window.resizable(False, False)
        
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - 150
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - 60
        capture_window.geometry(f'+{x}+{y}')
        
        container = ctk.CTkFrame(capture_window, fg_color='transparent')
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text='请按下要设置的按键...', font=Theme.get_font('base')).pack(pady=(0, 10))
        
        key_display = ctk.CTkEntry(container, width=100, height=32, justify='center', font=Theme.get_font('lg'))
        key_display.pack()
        key_display.insert(0, '...')
        
        def on_key_press(event):
            key_name = event.keysym.lower()
            if key_name == 'escape':
                capture_window.destroy()
                return
            
            entry.configure(state='normal')
            entry.delete(0, 'end')
            entry.insert(0, key_name)
            entry.configure(state='disabled')
            capture_window.destroy()
            self._show_notification('按键设置', f'已设置为: {key_name}', 'success')
        
        capture_window.bind('<Key>', on_key_press)
        capture_window.focus_set()
        capture_window.grab_set()
    
    def _create_ocr_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.pages['ocr'] = page
        
        top_frame = ctk.CTkFrame(page, fg_color='transparent')
        top_frame.pack(fill='x', pady=(0, 10))
        
        add_btn = AnimatedButton(top_frame, text='+ 新增识别组', font=Theme.get_font('sm'), height=28,
                                corner_radius=6, fg_color=Theme.COLORS['primary'], 
                                hover_color=Theme.COLORS['primary_hover'],
                                command=lambda: self._show_notification('添加', '已添加新识别组', 'info'))
        add_btn.pack(side='left')
        
        scroll_frame = ctk.CTkScrollableFrame(page)
        scroll_frame.pack(fill='both', expand=True)
        
        self.ocr_groups = []
        for i in range(2):
            self._create_ocr_group(scroll_frame, i)
    
    def _create_ocr_group(self, parent, index):
        enabled_var = ctk.BooleanVar(value=False)
        
        group_frame = CardFrame(parent, fg_color='#ffffff', border_width=1, border_color='#E5E7EB')
        group_frame.pack(fill='x', pady=(0, 10))
        
        header = ctk.CTkFrame(group_frame, fg_color='transparent')
        header.pack(fill='x', padx=10, pady=(8, 4))
        
        self._create_section_title(header, f'识别组 {index + 1}', level=2).pack(side='left')
        
        switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                              command=lambda: self._toggle_group_bg(group_frame, enabled_var.get()))
        switch.pack(side='left', padx=(8, 0))
        
        delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                                   fg_color=Theme.COLORS['error'], hover_color='#DC2626', press_color='#B91C1C',
                                   corner_radius=4, command=lambda: self._show_notification('删除', '已删除识别组', 'warning'))
        delete_btn.pack(side='right')
        
        self._create_divider(group_frame)
        
        row1 = ctk.CTkFrame(group_frame, fg_color='transparent')
        row1.pack(fill='x', padx=10, pady=4)
        
        select_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24, corner_radius=4,
                                   fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                                   command=lambda: self._show_notification('选择', '请在屏幕上选择区域', 'info'))
        select_btn.pack(side='left', padx=(0, 4))
        region_entry = ctk.CTkEntry(row1, placeholder_text='未选择区域', width=130, height=24, state='disabled')
        region_entry.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        key_entry = self._create_key_input_with_button(row1, 'equal', 50)
        
        ctk.CTkLabel(row1, text='时长:', font=Theme.get_font('xs')).pack(side='left', padx=(8, 0))
        delay_min = self._create_numeric_entry(row1, '300', 35)
        delay_min.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='-', font=Theme.get_font('xs')).pack(side='left')
        delay_max = self._create_numeric_entry(row1, '500', 35)
        delay_max.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='ms', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        alarm_var = ctk.BooleanVar(value=False)
        alarm_frame = ctk.CTkFrame(row1, fg_color='transparent')
        alarm_frame.pack(side='left')
        ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(alarm_frame, text='', width=36, variable=alarm_var).pack(side='left')
        
        row2 = ctk.CTkFrame(group_frame, fg_color='transparent')
        row2.pack(fill='x', padx=10, pady=(4, 8))
        
        ctk.CTkLabel(row2, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
        interval_entry = self._create_numeric_entry(row2, '5', 35)
        interval_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row2, text='暂停:', font=Theme.get_font('xs')).pack(side='left')
        pause_entry = self._create_numeric_entry(row2, '180', 40)
        pause_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row2, text='关键词:', font=Theme.get_font('xs')).pack(side='left')
        keywords_entry = ctk.CTkEntry(row2, width=100, height=24)
        keywords_entry.insert(0, 'men,door')
        keywords_entry.pack(side='left', padx=(2, 8))
        
        ctk.CTkLabel(row2, text='语言:', font=Theme.get_font('xs')).pack(side='left')
        lang_menu = ctk.CTkOptionMenu(row2, values=['eng', 'chi_sim', 'chi_tra'], width=70, height=24)
        lang_menu.pack(side='left', padx=(2, 8))
        
        click_var = ctk.BooleanVar(value=True)
        click_frame = ctk.CTkFrame(row2, fg_color='transparent')
        click_frame.pack(side='left')
        ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(click_frame, text='', width=36, variable=click_var).pack(side='left')
        
        self.ocr_groups.append({
            'frame': group_frame, 'enabled': enabled_var, 'region': region_entry, 'interval': interval_entry,
            'pause': pause_entry, 'key': key_entry, 'delay_min': delay_min, 'delay_max': delay_max,
            'alarm': alarm_var, 'keywords': keywords_entry, 'lang': lang_menu, 'click': click_var
        })
    
    def _create_timed_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.pages['timed'] = page
        
        top_frame = ctk.CTkFrame(page, fg_color='transparent')
        top_frame.pack(fill='x', pady=(0, 10))
        
        add_btn = AnimatedButton(top_frame, text='+ 新增定时组', font=Theme.get_font('sm'), height=28,
                                corner_radius=6, fg_color=Theme.COLORS['primary'],
                                hover_color=Theme.COLORS['primary_hover'],
                                command=lambda: self._show_notification('添加', '已添加新定时组', 'info'))
        add_btn.pack(side='left')
        
        scroll_frame = ctk.CTkScrollableFrame(page)
        scroll_frame.pack(fill='both', expand=True)
        
        self.timed_groups = []
        for i in range(3):
            self._create_timed_group(scroll_frame, i)
    
    def _create_timed_group(self, parent, index):
        enabled_var = ctk.BooleanVar(value=False)
        
        group_frame = CardFrame(parent, fg_color='#ffffff', border_width=1, border_color='#E5E7EB')
        group_frame.pack(fill='x', pady=(0, 10))
        
        header = ctk.CTkFrame(group_frame, fg_color='transparent')
        header.pack(fill='x', padx=10, pady=(8, 4))
        
        self._create_section_title(header, f'定时组 {index + 1}', level=2).pack(side='left')
        
        switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                              command=lambda: self._toggle_group_bg(group_frame, enabled_var.get()))
        switch.pack(side='left', padx=(8, 0))
        
        delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                                   fg_color=Theme.COLORS['error'], hover_color='#DC2626', press_color='#B91C1C',
                                   corner_radius=4, command=lambda: self._show_notification('删除', '已删除定时组', 'warning'))
        delete_btn.pack(side='right')
        
        self._create_divider(group_frame)
        
        row1 = ctk.CTkFrame(group_frame, fg_color='transparent')
        row1.pack(fill='x', padx=10, pady=(4, 8))
        
        ctk.CTkLabel(row1, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
        interval_entry = self._create_numeric_entry(row1, str(10 * (index + 1)), 35)
        interval_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        key_entry = self._create_key_input_with_button(row1, ['space', 'enter', 'tab'][index % 3], 50)
        
        ctk.CTkLabel(row1, text='时长:', font=Theme.get_font('xs')).pack(side='left', padx=(8, 0))
        delay_min = self._create_numeric_entry(row1, '300', 35)
        delay_min.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='-', font=Theme.get_font('xs')).pack(side='left')
        delay_max = self._create_numeric_entry(row1, '500', 35)
        delay_max.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='ms', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        click_var = ctk.BooleanVar(value=False)
        click_frame = ctk.CTkFrame(row1, fg_color='transparent')
        click_frame.pack(side='left')
        ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(click_frame, text='', width=36, variable=click_var).pack(side='left', padx=(0, 6))
        
        pos_btn = AnimatedButton(row1, text='位置', font=Theme.get_font('xs'), width=40, height=24, corner_radius=4,
                                fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                                command=lambda: self._show_notification('选择', '请在屏幕上点击位置', 'info'))
        pos_btn.pack(side='left', padx=(0, 4))
        pos_entry = ctk.CTkEntry(row1, placeholder_text='未选择', width=80, height=24, state='disabled')
        pos_entry.pack(side='left', padx=(0, 8))
        
        alarm_var = ctk.BooleanVar(value=False)
        alarm_frame = ctk.CTkFrame(row1, fg_color='transparent')
        alarm_frame.pack(side='left')
        ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(alarm_frame, text='', width=36, variable=alarm_var).pack(side='left')
        
        self.timed_groups.append({
            'frame': group_frame, 'enabled': enabled_var, 'interval': interval_entry, 'key': key_entry,
            'delay_min': delay_min, 'delay_max': delay_max, 'alarm': alarm_var, 'click': click_var, 'pos': pos_entry
        })
    
    def _create_number_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.pages['number'] = page
        
        top_frame = ctk.CTkFrame(page, fg_color='transparent')
        top_frame.pack(fill='x', pady=(0, 10))
        
        add_btn = AnimatedButton(top_frame, text='+ 新增识别组', font=Theme.get_font('sm'), height=28,
                                corner_radius=6, fg_color=Theme.COLORS['primary'],
                                hover_color=Theme.COLORS['primary_hover'],
                                command=lambda: self._show_notification('添加', '已添加新识别组', 'info'))
        add_btn.pack(side='left')
        
        scroll_frame = ctk.CTkScrollableFrame(page)
        scroll_frame.pack(fill='both', expand=True)
        
        self.number_regions = []
        for i in range(2):
            self._create_number_region(scroll_frame, i)
    
    def _create_number_region(self, parent, index):
        enabled_var = ctk.BooleanVar(value=False)
        
        group_frame = CardFrame(parent, fg_color='#ffffff', border_width=1, border_color='#E5E7EB')
        group_frame.pack(fill='x', pady=(0, 10))
        
        header = ctk.CTkFrame(group_frame, fg_color='transparent')
        header.pack(fill='x', padx=10, pady=(8, 4))
        
        self._create_section_title(header, f'识别组 {index + 1}', level=2).pack(side='left')
        
        switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                              command=lambda: self._toggle_group_bg(group_frame, enabled_var.get()))
        switch.pack(side='left', padx=(8, 0))
        
        delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                                   fg_color=Theme.COLORS['error'], hover_color='#DC2626', press_color='#B91C1C',
                                   corner_radius=4, command=lambda: self._show_notification('删除', '已删除识别组', 'warning'))
        delete_btn.pack(side='right')
        
        self._create_divider(group_frame)
        
        row1 = ctk.CTkFrame(group_frame, fg_color='transparent')
        row1.pack(fill='x', padx=10, pady=(4, 8))
        
        select_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24, corner_radius=4,
                                   fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                                   command=lambda: self._show_notification('选择', '请在屏幕上选择区域', 'info'))
        select_btn.pack(side='left', padx=(0, 4))
        region_entry = ctk.CTkEntry(row1, placeholder_text='未选择区域', width=130, height=24, state='disabled')
        region_entry.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='阈值:', font=Theme.get_font('xs')).pack(side='left')
        threshold_entry = self._create_numeric_entry(row1, str(500 * (index + 1)), 50)
        threshold_entry.pack(side='left', padx=(2, 8))
        
        ctk.CTkLabel(row1, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        key_entry = self._create_key_input_with_button(row1, ['f1', 'f2'][index], 50)
        
        ctk.CTkLabel(row1, text='时长:', font=Theme.get_font('xs')).pack(side='left', padx=(8, 0))
        delay_min = self._create_numeric_entry(row1, '100', 35)
        delay_min.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='-', font=Theme.get_font('xs')).pack(side='left')
        delay_max = self._create_numeric_entry(row1, '200', 35)
        delay_max.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='ms', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        alarm_var = ctk.BooleanVar(value=False)
        alarm_frame = ctk.CTkFrame(row1, fg_color='transparent')
        alarm_frame.pack(side='left')
        ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(alarm_frame, text='', width=36, variable=alarm_var).pack(side='left')
        
        self.number_regions.append({
            'frame': group_frame, 'enabled': enabled_var, 'region': region_entry, 'threshold': threshold_entry,
            'key': key_entry, 'delay_min': delay_min, 'delay_max': delay_max, 'alarm': alarm_var
        })
    
    def _toggle_group_bg(self, frame, enabled):
        if enabled:
            frame.configure(fg_color=Theme.COLORS['info_light'], border_color=Theme.COLORS['primary'])
        else:
            frame.configure(fg_color='#ffffff', border_color='#E5E7EB')
    
    def _create_script_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.pages['script'] = page
        
        main_frame = ctk.CTkFrame(page, fg_color='transparent')
        main_frame.pack(fill='both', expand=True)
        
        left_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 8))
        
        key_frame = CardFrame(left_frame, border_width=1, border_color='#E5E7EB')
        key_frame.pack(fill='x', pady=(0, 8))
        self._create_section_title(key_frame, '按键命令', level=2).pack(anchor='w', padx=10, pady=(8, 4))
        self._create_divider(key_frame)
        key_row = ctk.CTkFrame(key_frame, fg_color='transparent')
        key_row.pack(fill='x', padx=10, pady=(4, 8))
        ctk.CTkLabel(key_row, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        self.key_var = self._create_key_input_with_button(key_row, '1', 50)
        ctk.CTkLabel(key_row, text='类型:', font=Theme.get_font('xs')).pack(side='left', padx=(8, 0))
        self.key_type = ctk.CTkOptionMenu(key_row, values=['KeyDown', 'KeyUp'], width=80, height=24)
        self.key_type.pack(side='left', padx=(2, 6))
        AnimatedButton(key_row, text='插入', font=Theme.get_font('xs'), width=50, height=24, corner_radius=4,
                      fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                      command=lambda: self._show_notification('插入', '已插入按键命令', 'success')).pack(side='left')
        
        delay_frame = CardFrame(left_frame, border_width=1, border_color='#E5E7EB')
        delay_frame.pack(fill='x', pady=(0, 8))
        self._create_section_title(delay_frame, '延迟命令', level=2).pack(anchor='w', padx=10, pady=(8, 4))
        self._create_divider(delay_frame)
        delay_row = ctk.CTkFrame(delay_frame, fg_color='transparent')
        delay_row.pack(fill='x', padx=10, pady=(4, 8))
        ctk.CTkLabel(delay_row, text='延迟(ms):', font=Theme.get_font('xs')).pack(side='left')
        self.delay_entry = self._create_numeric_entry(delay_row, '250', 60)
        self.delay_entry.pack(side='left', padx=(2, 6))
        AnimatedButton(delay_row, text='插入', font=Theme.get_font('xs'), width=50, height=24, corner_radius=4,
                      fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                      command=lambda: self._show_notification('插入', '已插入延迟命令', 'success')).pack(side='left')
        
        mouse_frame = CardFrame(left_frame, border_width=1, border_color='#E5E7EB')
        mouse_frame.pack(fill='x', pady=(0, 8))
        self._create_section_title(mouse_frame, '鼠标命令', level=2).pack(anchor='w', padx=10, pady=(8, 4))
        self._create_divider(mouse_frame)
        mouse_row = ctk.CTkFrame(mouse_frame, fg_color='transparent')
        mouse_row.pack(fill='x', padx=10, pady=(4, 8))
        ctk.CTkLabel(mouse_row, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        self.mouse_btn = ctk.CTkOptionMenu(mouse_row, values=['Left', 'Right', 'Middle'], width=60, height=24)
        self.mouse_btn.pack(side='left', padx=(2, 6))
        ctk.CTkLabel(mouse_row, text='操作:', font=Theme.get_font('xs')).pack(side='left')
        self.mouse_action = ctk.CTkOptionMenu(mouse_row, values=['Down', 'Up'], width=60, height=24)
        self.mouse_action.pack(side='left', padx=(2, 6))
        AnimatedButton(mouse_row, text='插入', font=Theme.get_font('xs'), width=50, height=24, corner_radius=4,
                      fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                      command=lambda: self._show_notification('插入', '已插入鼠标命令', 'success')).pack(side='left')
        
        mouse_row2 = ctk.CTkFrame(mouse_frame, fg_color='transparent')
        mouse_row2.pack(fill='x', padx=10, pady=(0, 8))
        AnimatedButton(mouse_row2, text='选择坐标点', font=Theme.get_font('xs'), height=24, corner_radius=4,
                      fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                      command=lambda: self._show_notification('选择', '请在屏幕上点击', 'info')).pack(fill='x')
        
        combo_frame = CardFrame(left_frame, border_width=1, border_color='#E5E7EB')
        combo_frame.pack(fill='x', pady=(0, 8))
        self._create_section_title(combo_frame, '组合按键', level=2).pack(anchor='w', padx=10, pady=(8, 4))
        self._create_divider(combo_frame)
        combo_row = ctk.CTkFrame(combo_frame, fg_color='transparent')
        combo_row.pack(fill='x', padx=10, pady=(4, 8))
        ctk.CTkLabel(combo_row, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        self.combo_key = self._create_key_input_with_button(combo_row, '1', 50)
        ctk.CTkLabel(combo_row, text='按键延迟:', font=Theme.get_font('xs')).pack(side='left', padx=(8, 0))
        self.combo_delay = self._create_numeric_entry(combo_row, '2500', 50)
        self.combo_delay.pack(side='left', padx=(2, 6))
        ctk.CTkLabel(combo_row, text='抬起延迟:', font=Theme.get_font('xs')).pack(side='left')
        self.combo_after = self._create_numeric_entry(combo_row, '300', 50)
        self.combo_after.pack(side='left', padx=(2, 6))
        AnimatedButton(combo_row, text='插入', font=Theme.get_font('xs'), width=50, height=24, corner_radius=4,
                      fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                      command=lambda: self._show_notification('插入', '已插入组合命令', 'success')).pack(side='left')
        
        ctrl_frame = CardFrame(left_frame, border_width=1, border_color='#E5E7EB')
        ctrl_frame.pack(fill='x', pady=(0, 8))
        self._create_section_title(ctrl_frame, '脚本控制', level=2).pack(anchor='w', padx=10, pady=(8, 4))
        self._create_divider(ctrl_frame)
        ctrl_row = ctk.CTkFrame(ctrl_frame, fg_color='transparent')
        ctrl_row.pack(fill='x', padx=10, pady=(4, 8))
        AnimatedButton(ctrl_row, text='开始录制', font=Theme.get_font('xs'), height=24, corner_radius=4,
                      fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                      command=lambda: self._show_notification('录制', '开始录制', 'info')).pack(side='left', fill='x', expand=True, padx=(0, 4))
        AnimatedButton(ctrl_row, text='停止录制', font=Theme.get_font('xs'), height=24, fg_color=Theme.COLORS['error'], corner_radius=4,
                      hover_color='#DC2626', press_color='#B91C1C',
                      command=lambda: self._show_notification('录制', '停止录制', 'warning')).pack(side='left', fill='x', expand=True)
        ctrl_row2 = ctk.CTkFrame(ctrl_frame, fg_color='transparent')
        ctrl_row2.pack(fill='x', padx=10, pady=(0, 8))
        AnimatedButton(ctrl_row2, text='清空', font=Theme.get_font('xs'), height=24, fg_color='transparent',
                      text_color=Theme.COLORS['primary'], border_width=1, corner_radius=4,
                      hover_color=Theme.COLORS['info_light'],
                      command=lambda: self.script_text.delete('1.0', 'end')).pack(side='left', fill='x', expand=True, padx=(0, 4))
        AnimatedButton(ctrl_row2, text='导入', font=Theme.get_font('xs'), height=24, corner_radius=4,
                      fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                      command=lambda: self._show_notification('导入', '选择脚本文件', 'info')).pack(side='left', fill='x', expand=True, padx=(0, 4))
        AnimatedButton(ctrl_row2, text='导出', font=Theme.get_font('xs'), height=24, fg_color=Theme.COLORS['success'], corner_radius=4,
                      hover_color='#16A34A',
                      command=lambda: self._show_notification('导出', '脚本已导出', 'success')).pack(side='left', fill='x', expand=True)
        
        right_frame = ctk.CTkFrame(main_frame, width=400)
        right_frame.pack(side='left', fill='both', expand=True)
        right_frame.pack_propagate(False)
        
        self.script_tabview = ctk.CTkTabview(right_frame)
        self.script_tabview.pack(fill='both', expand=True, padx=4, pady=4)
        
        editor_tab = self.script_tabview.add('📜 脚本编辑')
        self.script_text = ctk.CTkTextbox(editor_tab, font=('Consolas', 10))
        self.script_text.pack(fill='both', expand=True, padx=4, pady=4)
        self.script_text.insert('1.0', '# 脚本示例\nKeyDown "enter", 1\nDelay 250\nKeyUp "enter", 1\n')
        
        color_tab = self.script_tabview.add('🎨 颜色识别')
        color_content = ctk.CTkFrame(color_tab, fg_color='transparent')
        color_content.pack(fill='both', expand=True, padx=8, pady=8)
        
        color_row1 = ctk.CTkFrame(color_content, fg_color='transparent')
        color_row1.pack(fill='x', pady=4)
        self.color_enabled = ctk.BooleanVar(value=False)
        color_enable_frame = ctk.CTkFrame(color_row1, fg_color='transparent')
        color_enable_frame.pack(side='left')
        ctk.CTkLabel(color_enable_frame, text='启用颜色识别', font=Theme.get_font('sm')).pack(side='left', padx=(0, 4))
        ctk.CTkSwitch(color_enable_frame, text='', width=36, variable=self.color_enabled).pack(side='left')
        
        color_row2 = ctk.CTkFrame(color_content, fg_color='transparent')
        color_row2.pack(fill='x', pady=4)
        AnimatedButton(color_row2, text='选择区域', font=Theme.get_font('xs'), width=60, height=24, corner_radius=4,
                      fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                      command=lambda: self._show_notification('选择', '请在屏幕上选择区域', 'info')).pack(side='left', padx=(0, 4))
        self.color_region = ctk.CTkEntry(color_row2, placeholder_text='未选择区域', width=120, height=24, state='disabled')
        self.color_region.pack(side='left')
        
        color_row3 = ctk.CTkFrame(color_content, fg_color='transparent')
        color_row3.pack(fill='x', pady=4)
        AnimatedButton(color_row3, text='选择颜色', font=Theme.get_font('xs'), width=60, height=24, corner_radius=4,
                      fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                      command=lambda: self._show_notification('选择', '请在屏幕上选择颜色', 'info')).pack(side='left', padx=(0, 4))
        self.color_value = ctk.CTkEntry(color_row3, placeholder_text='未选择颜色', width=80, height=24, state='disabled')
        self.color_value.pack(side='left', padx=(0, 8))
        ctk.CTkLabel(color_row3, text='容差:', font=Theme.get_font('xs')).pack(side='left')
        self.color_tolerance = self._create_numeric_entry(color_row3, '10', 40)
        self.color_tolerance.pack(side='left', padx=(2, 8))
        ctk.CTkLabel(color_row3, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
        self.color_interval = self._create_numeric_entry(color_row3, '5', 40)
        self.color_interval.pack(side='left', padx=(2, 0))
        ctk.CTkLabel(color_row3, text='秒', font=Theme.get_font('xs')).pack(side='left')
        
        ctk.CTkLabel(color_content, text='执行命令:', font=Theme.get_font('sm')).pack(anchor='w', pady=(8, 2))
        self.color_commands = ctk.CTkTextbox(color_content, font=('Consolas', 10), height=100)
        self.color_commands.pack(fill='both', expand=True)
    
    def _create_settings_page(self):
        page = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.pages['settings'] = page
        
        scroll_frame = ctk.CTkScrollableFrame(page)
        scroll_frame.pack(fill='both', expand=True)
        
        tess_frame = CardFrame(scroll_frame, border_width=1, border_color='#E5E7EB')
        tess_frame.pack(fill='x', pady=(0, 10))
        self._create_section_title(tess_frame, 'Tesseract OCR 设置', level=1).pack(anchor='w', padx=12, pady=(10, 6))
        self._create_divider(tess_frame)
        tess_row = ctk.CTkFrame(tess_frame, fg_color='transparent')
        tess_row.pack(fill='x', padx=12, pady=(4, 10))
        ctk.CTkLabel(tess_row, text='路径:', font=Theme.get_font('sm')).pack(side='left')
        self.tesseract_path = ctk.CTkEntry(tess_row, placeholder_text='选择 tesseract.exe 路径', height=28, state='disabled')
        self.tesseract_path.pack(side='left', fill='x', expand=True, padx=(6, 6))
        AnimatedButton(tess_row, text='浏览', font=Theme.get_font('xs'), width=50, height=28, corner_radius=4,
                      fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                      command=lambda: self._show_notification('浏览', '选择Tesseract路径', 'info')).pack(side='left')
        
        alarm_frame = CardFrame(scroll_frame, border_width=1, border_color='#E5E7EB')
        alarm_frame.pack(fill='x', pady=(0, 10))
        self._create_section_title(alarm_frame, '报警设置', level=1).pack(anchor='w', padx=12, pady=(10, 6))
        self._create_divider(alarm_frame)
        alarm_row1 = ctk.CTkFrame(alarm_frame, fg_color='transparent')
        alarm_row1.pack(fill='x', padx=12, pady=4)
        ctk.CTkLabel(alarm_row1, text='声音:', font=Theme.get_font('sm')).pack(side='left')
        self.alarm_sound = ctk.CTkEntry(alarm_row1, placeholder_text='选择报警声音文件', height=28, state='disabled')
        self.alarm_sound.pack(side='left', fill='x', expand=True, padx=(6, 6))
        AnimatedButton(alarm_row1, text='浏览', font=Theme.get_font('xs'), width=50, height=28, corner_radius=4,
                      fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                      command=lambda: self._show_notification('浏览', '选择声音文件', 'info')).pack(side='left')
        
        alarm_row2 = ctk.CTkFrame(alarm_frame, fg_color='transparent')
        alarm_row2.pack(fill='x', padx=12, pady=(4, 10))
        ctk.CTkLabel(alarm_row2, text='音量:', font=Theme.get_font('sm')).pack(side='left')
        self.volume_slider = ctk.CTkSlider(alarm_row2, from_=0, to=100, number_of_steps=100, width=200)
        self.volume_slider.set(70)
        self.volume_slider.pack(side='left', padx=(6, 6))
        self.volume_label = ctk.CTkLabel(alarm_row2, text='70%', font=Theme.get_font('sm'), width=40)
        self.volume_label.pack(side='left')
        
        shortcut_frame = CardFrame(scroll_frame, border_width=1, border_color='#E5E7EB')
        shortcut_frame.pack(fill='x', pady=(0, 10))
        self._create_section_title(shortcut_frame, '快捷键设置', level=1).pack(anchor='w', padx=12, pady=(10, 6))
        self._create_divider(shortcut_frame)
        
        shortcuts = [('开始/停止:', 'F10'), ('暂停/继续:', 'F12'), ('选择区域:', 'F11')]
        self.shortcut_vars = {}
        for label, default in shortcuts:
            row = ctk.CTkFrame(shortcut_frame, fg_color='transparent')
            row.pack(fill='x', padx=12, pady=4)
            ctk.CTkLabel(row, text=label, font=Theme.get_font('sm')).pack(side='left')
            entry = self._create_key_input_with_button(row, default, 80)
            self.shortcut_vars[label] = entry
        
        ctk.CTkFrame(shortcut_frame, height=6, fg_color='transparent').pack()
        
        config_frame = CardFrame(scroll_frame, border_width=1, border_color='#E5E7EB')
        config_frame.pack(fill='x', pady=(0, 10))
        self._create_section_title(config_frame, '配置管理', level=1).pack(anchor='w', padx=12, pady=(10, 6))
        self._create_divider(config_frame)
        config_row = ctk.CTkFrame(config_frame, fg_color='transparent')
        config_row.pack(fill='x', padx=12, pady=(4, 10))
        AnimatedButton(config_row, text='💾 保存配置', font=Theme.get_font('sm'), height=32, corner_radius=6,
                      fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                      command=lambda: self._show_notification('保存', '配置已保存', 'success')).pack(side='left', fill='x', expand=True, padx=(0, 8))
        AnimatedButton(config_row, text='🔄 重置配置', font=Theme.get_font('sm'), height=32, fg_color=Theme.COLORS['warning'], corner_radius=6,
                      hover_color='#D97706', press_color='#B45309',
                      command=lambda: self._show_notification('重置', '配置已重置', 'warning')).pack(side='left', fill='x', expand=True)
    
    def _show_loading_and_execute(self, message, callback):
        self._loading_overlay = LoadingOverlay(self.content_area, message)
        self._loading_overlay.show()
        self.root.after(1500, self._execute_callback, callback)
    
    def _execute_callback(self, callback):
        if callback:
            callback()
        if self._loading_overlay:
            self._loading_overlay.hide()
    
    def _check_update(self):
        self._show_notification('检查更新', '已是最新版本', 'success')
    
    def _start_all_modules(self):
        for key in self.module_indicators:
            self.module_indicators[key].configure(text_color=Theme.COLORS['success'])
        self._show_notification('操作', '启动成功', 'success')
    
    def _stop_all_modules(self):
        for key in self.module_indicators:
            self.module_indicators[key].configure(text_color='#9CA3AF')
        self._show_notification('操作', '已停止', 'warning')
    
    def _show_page(self, page_id):
        for pid, page in self.pages.items():
            if pid == page_id:
                page.pack(fill='both', expand=True)
            else:
                page.pack_forget()
        self._set_nav_active(page_id)
        self._current_page = page_id
    
    def _navigate_to(self, page_id):
        self._show_page(page_id)
    
    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = 'Dark' if current == 'Light' else 'Light'
        ctk.set_appearance_mode(new_mode)
    
    def _show_notification(self, title, message, notification_type='info'):
        self._create_notification(title, message, notification_type)
    
    def _create_notification(self, title, message, notification_type='info'):
        type_colors = {'info': Theme.COLORS['info'], 'success': Theme.COLORS['success'],
                      'warning': Theme.COLORS['warning'], 'error': Theme.COLORS['error']}
        color = type_colors.get(notification_type, Theme.COLORS['info'])
        
        notif = ctk.CTkToplevel(self.root)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        
        self.root.update_idletasks()
        master_x = self.root.winfo_rootx()
        master_y = self.root.winfo_rooty()
        master_width = self.root.winfo_width()
        
        width, height = 280, 70
        x = master_x + master_width - width - 20
        y = master_y + 60
        notif.geometry(f'{width}x{height}+{x}+{y}')
        
        container = ctk.CTkFrame(notif, corner_radius=8, border_width=1, border_color='#E5E7EB')
        container.pack(fill='both', expand=True, padx=4, pady=4)
        
        indicator = ctk.CTkFrame(container, width=4, corner_radius=0, fg_color=color)
        indicator.pack(side='left', fill='y')
        
        content = ctk.CTkFrame(container, fg_color='transparent')
        content.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(content, text=title, font=Theme.get_font('sm'), anchor='w').pack(fill='x')
        ctk.CTkLabel(content, text=message, font=Theme.get_font('xs'), text_color=Theme.COLORS['text_secondary'], anchor='w').pack(fill='x', pady=(4, 0))
        
        notif.after(3000, notif.destroy)
    
    def run(self):
        self.root.mainloop()


def main():
    app = AppTemplate()
    app.run()


if __name__ == '__main__':
    main()
