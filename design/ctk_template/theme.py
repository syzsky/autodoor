import customtkinter as ctk
import platform


class Theme:
    SYSTEM = platform.system()
    
    COLORS = {
        'primary': '#3B82F6',
        'primary_hover': '#2563EB',
        'primary_light': '#60A5FA',
        
        'success': '#10B981',
        'success_light': '#D1FAE5',
        'warning': '#F59E0B',
        'warning_light': '#FEF3C7',
        'error': '#EF4444',
        'error_light': '#FEE2E2',
        'info': '#3B82F6',
        'info_light': '#DBEAFE',
        
        'text_primary': '#1A1A1A',
        'text_secondary': '#6B7280',
        'text_muted': '#9CA3AF',
        
        'border': '#E5E5E5',
        'border_dark': '#404040',
    }
    
    DARK_COLORS = {
        'text_primary': '#FFFFFF',
        'text_secondary': '#9CA3AF',
        'text_muted': '#6B7280',
        'border': '#404040',
    }
    
    DIMENSIONS = {
        'sidebar_width': 220,
        'header_height': 50,
        'footer_height': 36,
        'card_corner_radius': 12,
        'button_corner_radius': 8,
        'border_width': 1,
    }
    
    FONTS = {
        'family': {
            'Windows': 'Microsoft YaHei UI',
            'Darwin': 'PingFang SC',
            'Linux': 'Noto Sans CJK SC'
        },
        'sizes': {
            'xs': 11,
            'sm': 12,
            'base': 14,
            'lg': 16,
            'xl': 18,
            '2xl': 20,
            '3xl': 24,
        }
    }
    
    @classmethod
    def get_font_family(cls):
        return cls.FONTS['family'].get(cls.SYSTEM, 'Arial')
    
    @classmethod
    def get_font(cls, size_key='base'):
        family = cls.get_font_family()
        size = cls.FONTS['sizes'].get(size_key, 14)
        return (family, size)
    
    @classmethod
    def is_dark_mode(cls):
        return ctk.get_appearance_mode() == 'Dark'
    
    @classmethod
    def get_color(cls, key):
        if cls.is_dark_mode() and key in cls.DARK_COLORS:
            return cls.DARK_COLORS[key]
        return cls.COLORS.get(key, '#000000')


def init_theme():
    ctk.set_appearance_mode('System')
    ctk.set_default_color_theme('blue')
