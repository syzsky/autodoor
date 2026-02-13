import customtkinter as ctk
from theme import Theme


class ModernCard(ctk.CTkFrame):
    def __init__(self, master, title='', show_header=True, **kwargs):
        self._title = title
        self._show_header = show_header
        
        kwargs.setdefault('corner_radius', Theme.DIMENSIONS['card_corner_radius'])
        super().__init__(master, **kwargs)
        
        self._create_widgets()
    
    def _create_widgets(self):
        if self._show_header and self._title:
            self.header = ctk.CTkFrame(self, fg_color='transparent')
            self.header.pack(fill='x', padx=12, pady=(12, 0))
            
            self.title_label = ctk.CTkLabel(
                self.header,
                text=self._title,
                font=Theme.get_font('lg'),
            )
            self.title_label.pack(side='left')
            
            self.actions_frame = ctk.CTkFrame(self.header, fg_color='transparent')
            self.actions_frame.pack(side='right')
        
        self.body = ctk.CTkFrame(self, fg_color='transparent')
        self.body.pack(fill='both', expand=True, padx=12, pady=12)
    
    def add_action(self, text, command=None, style='primary'):
        if not hasattr(self, 'actions_frame'):
            return None
        
        fg_color = Theme.COLORS['primary'] if style == 'primary' else 'transparent'
        text_color = '#FFFFFF' if style == 'primary' else Theme.COLORS['primary']
        hover_color = Theme.COLORS['primary_hover'] if style == 'primary' else Theme.COLORS['info_light']
        
        btn = ctk.CTkButton(
            self.actions_frame,
            text=text,
            command=command,
            font=Theme.get_font('sm'),
            fg_color=fg_color,
            text_color=text_color,
            hover_color=hover_color,
            corner_radius=6,
            height=28,
        )
        btn.pack(side='left', padx=(8, 0))
        return btn


class StatusBadge(ctk.CTkLabel):
    STATUS_CONFIG = {
        'running': {'text': '运行中', 'color': Theme.COLORS['success'], 'bg': Theme.COLORS['success_light']},
        'paused': {'text': '已暂停', 'color': Theme.COLORS['warning'], 'bg': Theme.COLORS['warning_light']},
        'stopped': {'text': '已停止', 'color': Theme.COLORS['text_muted'], 'bg': '#F3F4F6'},
        'error': {'text': '错误', 'color': Theme.COLORS['error'], 'bg': Theme.COLORS['error_light']},
        'success': {'text': '成功', 'color': Theme.COLORS['success'], 'bg': Theme.COLORS['success_light']},
    }
    
    def __init__(self, master, status='stopped', **kwargs):
        self._status = status
        config = self.STATUS_CONFIG.get(status, self.STATUS_CONFIG['stopped'])
        
        super().__init__(
            master,
            text=config['text'],
            font=Theme.get_font('xs'),
            text_color=config['color'],
            fg_color=config['bg'],
            corner_radius=4,
            padx=8,
            pady=2,
            **kwargs
        )
    
    def set_status(self, status):
        self._status = status
        config = self.STATUS_CONFIG.get(status, self.STATUS_CONFIG['stopped'])
        self.configure(text=config['text'], text_color=config['color'], fg_color=config['bg'])


class StatCard(ctk.CTkFrame):
    def __init__(self, master, label='', value='0', value_style='default', **kwargs):
        self._label = label
        self._value = value
        self._value_style = value_style
        
        kwargs.setdefault('corner_radius', Theme.DIMENSIONS['card_corner_radius'])
        super().__init__(master, **kwargs)
        
        self._create_widgets()
    
    def _create_widgets(self):
        style_colors = {
            'default': Theme.COLORS['text_primary'],
            'success': Theme.COLORS['success'],
            'warning': Theme.COLORS['warning'],
            'error': Theme.COLORS['error'],
            'info': Theme.COLORS['info'],
        }
        color = style_colors.get(self._value_style, style_colors['default'])
        
        self.value_label = ctk.CTkLabel(
            self,
            text=str(self._value),
            font=Theme.get_font('3xl'),
            text_color=color,
        )
        self.value_label.pack(pady=(16, 4))
        
        self.label_label = ctk.CTkLabel(
            self,
            text=self._label,
            font=Theme.get_font('sm'),
            text_color=Theme.COLORS['text_secondary'],
        )
        self.label_label.pack(pady=(0, 12))
    
    def set_value(self, value):
        self._value = str(value)
        self.value_label.configure(text=self._value)


class NavItem(ctk.CTkFrame):
    def __init__(self, master, text='', icon='', command=None, is_active=False, **kwargs):
        self._text = text
        self._icon = icon
        self._command = command
        self._is_active = is_active
        
        super().__init__(master, fg_color='transparent', corner_radius=0, **kwargs)
        
        self._create_widgets()
        self._bind_events()
        
        if self._is_active:
            self._set_active()
    
    def _create_widgets(self):
        self._indicator = ctk.CTkFrame(
            self,
            width=3,
            height=24,
            fg_color='transparent',
            corner_radius=0,
        )
        self._indicator.pack(side='left', padx=(8, 0), pady=8)
        
        self._content = ctk.CTkFrame(self, fg_color='transparent')
        self._content.pack(side='left', fill='x', expand=True, padx=8, pady=8)
        
        display_text = f'{self._icon}  {self._text}' if self._icon else self._text
        
        self._label = ctk.CTkLabel(
            self._content,
            text=display_text,
            font=Theme.get_font('base'),
            text_color=Theme.COLORS['text_secondary'],
            anchor='w',
        )
        self._label.pack(fill='x')
    
    def _bind_events(self):
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        
        for child in self.winfo_children():
            child.bind('<Enter>', self._on_enter)
            child.bind('<Leave>', self._on_leave)
            child.bind('<Button-1>', self._on_click)
            
            for subchild in child.winfo_children():
                subchild.bind('<Enter>', self._on_enter)
                subchild.bind('<Leave>', self._on_leave)
                subchild.bind('<Button-1>', self._on_click)
    
    def _on_enter(self, event):
        if not self._is_active:
            self.configure(fg_color=Theme.COLORS['info_light'])
    
    def _on_leave(self, event):
        if not self._is_active:
            self.configure(fg_color='transparent')
    
    def _on_click(self, event):
        if self._command:
            self._command()
    
    def _set_active(self):
        self._is_active = True
        self.configure(fg_color=Theme.COLORS['info_light'])
        self._indicator.configure(fg_color=Theme.COLORS['primary'])
        self._label.configure(text_color=Theme.COLORS['primary'])
    
    def set_active(self, active=True):
        if active:
            self._set_active()
        else:
            self._is_active = False
            self.configure(fg_color='transparent')
            self._indicator.configure(fg_color='transparent')
            self._label.configure(text_color=Theme.COLORS['text_secondary'])


class Notification(ctk.CTkToplevel):
    def __init__(self, master, title='', message='', notification_type='info', duration=4000):
        super().__init__(master)
        
        self._title = title
        self._message = message
        self._type = notification_type
        self._duration = duration
        
        self._setup_window()
        self._create_widgets()
        
        if duration > 0:
            self.after(duration, self.destroy)
    
    def _setup_window(self):
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        self.update_idletasks()
        master_x = self.master.winfo_rootx()
        master_y = self.master.winfo_rooty()
        master_width = self.master.winfo_width()
        
        width = 320
        height = 80
        x = master_x + master_width - width - 20
        y = master_y + 70
        
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        type_colors = {
            'info': Theme.COLORS['info'],
            'success': Theme.COLORS['success'],
            'warning': Theme.COLORS['warning'],
            'error': Theme.COLORS['error'],
        }
        color = type_colors.get(self._type, Theme.COLORS['info'])
        
        container = ctk.CTkFrame(self, corner_radius=8, border_width=1)
        container.pack(fill='both', expand=True, padx=4, pady=4)
        
        self._indicator = ctk.CTkFrame(
            container,
            width=4,
            corner_radius=0,
            fg_color=color,
        )
        self._indicator.pack(side='left', fill='y')
        
        content = ctk.CTkFrame(container, fg_color='transparent')
        content.pack(side='left', fill='both', expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(
            content,
            text=self._title,
            font=Theme.get_font('sm'),
            anchor='w',
        ).pack(fill='x')
        
        ctk.CTkLabel(
            content,
            text=self._message,
            font=Theme.get_font('xs'),
            text_color=Theme.COLORS['text_secondary'],
            anchor='w',
        ).pack(fill='x', pady=(4, 0))
        
        close_btn = ctk.CTkButton(
            container,
            text='×',
            width=24,
            height=24,
            font=('Arial', 16),
            fg_color='transparent',
            text_color=Theme.COLORS['text_muted'],
            hover_color=Theme.COLORS['info_light'],
            command=self.destroy,
        )
        close_btn.pack(side='right', padx=8, pady=8)


class ModuleItem(ctk.CTkFrame):
    def __init__(self, master, name='', is_running=False, on_toggle=None, **kwargs):
        self._name = name
        self._is_running = is_running
        self._on_toggle = on_toggle
        
        super().__init__(master, fg_color='transparent', **kwargs)
        
        self._create_widgets()
    
    def _create_widgets(self):
        self._name_label = ctk.CTkLabel(
            self,
            text=self._name,
            font=Theme.get_font('base'),
            anchor='w',
        )
        self._name_label.pack(side='left')
        
        self._status = StatusBadge(
            self,
            status='running' if self._is_running else 'paused',
        )
        self._status.pack(side='right', padx=(0, 12))
        
        self._switch = ctk.CTkSwitch(
            self,
            text='',
            width=40,
            command=self._on_switch_toggle,
        )
        self._switch.pack(side='right')
        if self._is_running:
            self._switch.select()
    
    def _on_switch_toggle(self):
        self._is_running = not self._is_running
        self._status.set_status('running' if self._is_running else 'paused')
        if self._on_toggle:
            self._on_toggle(self._is_running)
