import customtkinter as ctk
from ui.theme import Theme


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
        kwargs.setdefault('corner_radius', Theme.DIMENSIONS['card_corner_radius'])
        kwargs.setdefault('border_width', 1)
        kwargs.setdefault('border_color', Theme.COLORS['border'])
        kwargs.setdefault('fg_color', Theme.COLORS['card_bg'])
        super().__init__(master, **kwargs)


class AnimatedButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        self._press_color = kwargs.pop('press_color', None)
        self._original_fg = kwargs.get('fg_color', Theme.COLORS['primary'])
        self._original_hover = kwargs.get('hover_color', Theme.COLORS['primary_hover'])
        
        if self._press_color is None:
            if isinstance(self._original_fg, str) and self._original_fg not in ['transparent']:
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
        if self._original_fg not in ['transparent']:
            self.configure(fg_color=self._press_color)
    
    def _on_release(self, event):
        if self._original_fg not in ['transparent']:
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


class Notification:
    def __init__(self, parent, title='通知', message='', notification_type='info'):
        self.parent = parent
        self.title = title
        self.message = message
        self.notification_type = notification_type
        
        self._create_notification()
    
    def _create_notification(self):
        type_colors = {
            'info': Theme.COLORS['info'],
            'success': Theme.COLORS['success'],
            'warning': Theme.COLORS['warning'],
            'error': Theme.COLORS['error']
        }
        color = type_colors.get(self.notification_type, Theme.COLORS['info'])
        
        notif = ctk.CTkToplevel(self.parent)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        
        self.parent.update_idletasks()
        master_x = self.parent.winfo_rootx()
        master_y = self.parent.winfo_rooty()
        master_width = self.parent.winfo_width()
        
        width, height = 280, 70
        x = master_x + master_width - width - 20
        y = master_y + 60
        notif.geometry(f'{width}x{height}+{x}+{y}')
        
        container = ctk.CTkFrame(notif, corner_radius=8, border_width=1, border_color=Theme.COLORS['border'])
        container.pack(fill='both', expand=True, padx=4, pady=4)
        
        indicator = ctk.CTkFrame(container, width=4, corner_radius=0, fg_color=color)
        indicator.pack(side='left', fill='y')
        
        content = ctk.CTkFrame(container, fg_color='transparent')
        content.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(content, text=self.title, font=Theme.get_font('sm'), anchor='w').pack(fill='x')
        ctk.CTkLabel(content, text=self.message, font=Theme.get_font('xs'), 
                    text_color=Theme.COLORS['text_secondary'], anchor='w').pack(fill='x', pady=(4, 0))
        
        notif.after(3000, notif.destroy)


def create_section_title(parent, text, level=1):
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


def create_divider(parent):
    divider = ctk.CTkFrame(parent, height=1, fg_color=Theme.COLORS['border'])
    divider.pack(fill='x', pady=8)
    return divider


def create_key_input_with_button(parent, default_value, width=50, on_capture=None):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(side='left')
    
    entry = ctk.CTkEntry(frame, width=width, height=24, state='disabled')
    entry.insert(0, default_value)
    entry.pack(side='left', padx=(2, 2))
    
    btn = AnimatedButton(frame, text='改', font=Theme.get_font('xs'), width=24, height=24, 
                        corner_radius=4, fg_color=Theme.COLORS['text_muted'],
                        hover_color=Theme.COLORS['text_secondary'])
    btn.pack(side='left')
    
    btn._entry = entry
    btn._on_capture = on_capture
    
    return entry, btn


def create_numeric_entry(parent, default_value='', width=40, **kwargs):
    entry = NumericEntry(parent, width=width, height=24, **kwargs)
    if default_value:
        entry.insert(0, str(default_value))
    return entry
