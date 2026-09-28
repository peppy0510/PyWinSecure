# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com

타이틀바와 사이드 메뉴가 쓰는 선 아이콘. 모두 size 를 한 변으로 하는
정사각형 안에 (cx, cy) 를 가운데 두고 그린다.
'''


import math
import wx


def get_pen(gc, colour, width):
    return gc.CreatePen(wx.GraphicsPenInfo(wx.Colour(colour)).Width(width)
                        .Cap(wx.CAP_ROUND).Join(wx.JOIN_ROUND))


def draw_glyph(gc, name, cx, cy, size, colour, width=None):
    handler = HANDLERS.get(name)
    if handler is None:
        return
    width = width or max(1.0, size * 0.085)
    gc.SetPen(get_pen(gc, colour, width))
    gc.SetBrush(wx.TRANSPARENT_BRUSH)
    handler(gc, cx, cy, size, wx.Colour(colour), width)


def draw_lock(gc, cx, cy, size, colour, width):
    body_width, body_height = size * 0.72, size * 0.48
    body_top = cy - size * 0.04
    gc.DrawRoundedRectangle(cx - body_width / 2, body_top, body_width, body_height,
                            size * 0.08)

    # 고리는 몸통 위로 반원을 올리고 양 끝을 몸통까지 곧게 내린다.
    arch = size * 0.22
    arch_cy = cy - size * 0.20
    path = gc.CreatePath()
    path.MoveToPoint(cx - arch, body_top)
    path.AddLineToPoint(cx - arch, arch_cy)
    path.AddArc(cx, arch_cy, arch, math.pi, 0, True)
    path.AddLineToPoint(cx + arch, body_top)
    gc.StrokePath(path)
    gc.StrokeLine(cx, body_top + body_height * 0.36, cx, body_top + body_height * 0.64)


def draw_eye(gc, cx, cy, size, colour, width):
    half, lid = size * 0.46, size * 0.40
    path = gc.CreatePath()
    path.MoveToPoint(cx - half, cy)
    path.AddCurveToPoint(cx - half * 0.5, cy - lid, cx + half * 0.5, cy - lid, cx + half, cy)
    path.AddCurveToPoint(cx + half * 0.5, cy + lid, cx - half * 0.5, cy + lid, cx - half, cy)
    path.CloseSubpath()
    gc.StrokePath(path)
    pupil = size * 0.13
    gc.DrawEllipse(cx - pupil, cy - pupil, pupil * 2, pupil * 2)


def draw_eye_off(gc, cx, cy, size, colour, width):
    draw_eye(gc, cx, cy, size, colour, width)
    arm = size * 0.40
    gc.StrokeLine(cx - arm, cy - arm, cx + arm, cy + arm)


def draw_settings(gc, cx, cy, size, colour, width):
    '''원에서 뻗는 살로 그리면 이 크기에서는 톱니바퀴가 아니라 해로 읽힌다.
    바깥선을 톱니 모양 그대로 두르고 가운데 축만 남긴다.'''
    outer, inner, hub = size * 0.48, size * 0.33, size * 0.15
    steps = 16

    path = gc.CreatePath()
    for step in range(steps):
        angle = math.radians(step * 360.0 / steps)
        radius = outer if step % 2 == 0 else inner
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        if step:
            path.AddLineToPoint(x, y)
        else:
            path.MoveToPoint(x, y)
    path.CloseSubpath()
    gc.StrokePath(path)
    gc.DrawEllipse(cx - hub, cy - hub, hub * 2, hub * 2)


def draw_menu(gc, cx, cy, size, colour, width):
    half = size * 0.42
    for offset in (-size * 0.30, 0.0, size * 0.30):
        gc.StrokeLine(cx - half, cy + offset, cx + half, cy + offset)


def draw_minimize(gc, cx, cy, size, colour, width):
    gc.StrokeLine(cx - size * 0.40, cy, cx + size * 0.40, cy)


def draw_maximize(gc, cx, cy, size, colour, width):
    span = size * 0.72
    gc.DrawRectangle(cx - span / 2, cy - span / 2, span, span)


def draw_restore(gc, cx, cy, size, colour, width):
    gc.DrawRectangle(cx - size * 0.38, cy - size * 0.22, size * 0.60, size * 0.60)
    # 뒤 사각형은 앞 사각형에 가려지는 두 변을 빼고 ㄱ 자로만 그린다.
    path = gc.CreatePath()
    path.MoveToPoint(cx - size * 0.22, cy - size * 0.22)
    path.AddLineToPoint(cx - size * 0.22, cy - size * 0.38)
    path.AddLineToPoint(cx + size * 0.38, cy - size * 0.38)
    path.AddLineToPoint(cx + size * 0.38, cy + size * 0.22)
    path.AddLineToPoint(cx + size * 0.22, cy + size * 0.22)
    gc.StrokePath(path)


def draw_close(gc, cx, cy, size, colour, width):
    arm = size * 0.36
    gc.StrokeLine(cx - arm, cy - arm, cx + arm, cy + arm)
    gc.StrokeLine(cx - arm, cy + arm, cx + arm, cy - arm)


HANDLERS = {
    'lock': draw_lock,
    'eye': draw_eye,
    'eye_off': draw_eye_off,
    'settings': draw_settings,
    'menu': draw_menu,
    'minimize': draw_minimize,
    'maximize': draw_maximize,
    'restore': draw_restore,
    'close': draw_close,
}
