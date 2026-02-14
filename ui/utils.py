from ui.theme import Theme


def update_group_style(group_frame, enabled):
    """更新组的样式"""
    if enabled:
        group_frame.configure(fg_color=Theme.COLORS['info_light'], 
                            border_color=Theme.COLORS['primary'])
    else:
        group_frame.configure(fg_color='#ffffff', 
                            border_color=Theme.COLORS['border'])
