# main_simulation.py
import pygame
import sys
import random
from config import *
from pedestrian_simulator import Pedestrian
from rsu_simulator import RSU
from traffic_light_controller import TrafficLightController

# --- Pygame 初始化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PI-BREPSC - Pedestrian Signal Simulation with Physical Information Fusion")
clock = pygame.time.Clock()
font_s = pygame.font.Font(DEFAULT_FONT_NAME, FONT_SIZE_SMALL)
font_m = pygame.font.Font(DEFAULT_FONT_NAME, FONT_SIZE_MEDIUM)
font_l = pygame.font.Font(DEFAULT_FONT_NAME, FONT_SIZE_LARGE)

# --- 仿真对象实例化 ---
rsu_unit = RSU(rsu_id="Intersection_RSU1", scanner_configs_dict=RSU_SCANNER_POSITIONS)
tlc_unit = TrafficLightController()
pedestrians_list = []
selected_pedestrian_id = None # 用于显示详细信息

# --- 辅助函数 ---
def draw_text(surface, text, pos, font, color=DARK_GREY, center_aligned=False):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if center_aligned:
        text_rect.center = pos
    else:
        text_rect.topleft = pos
    surface.blit(text_surf, text_rect)

def spawn_pedestrian(ped_id_counter, side="west", y_offset=0):
    """Spawns a pedestrian in the sidewalk area on the specified side and plans a path."""
    start_y = random.randint(int(H_CROSSWALK_RECT_NORTH.centery - ROAD_WIDTH*0.8), 
                             int(H_CROSSWALK_RECT_SOUTH.centery + ROAD_WIDTH*0.8)) + y_offset
    
    if side == "west":
        start_x = WAIT_AREA_WEST.left + PEDESTRIAN_RADIUS + 5
        target_wait_x = WAIT_AREA_WEST.right - PEDESTRIAN_RADIUS - 10
        target_wait_area_key = "WAIT_AREA_WEST"
        color = BLUE
    else: # east
        start_x = WAIT_AREA_EAST.right - PEDESTRIAN_RADIUS - 5
        target_wait_x = WAIT_AREA_EAST.left + PEDESTRIAN_RADIUS + 10
        target_wait_area_key = "WAIT_AREA_EAST"
        color = (0,100,200) # 深蓝

    ped = Pedestrian(id_num=ped_id_counter, start_pos=(start_x, start_y), color=color, target_wait_area_key=target_wait_area_key)
    ped.set_path_to_point((target_wait_x, start_y)) # 移动到等待区边缘
    pedestrians_list.append(ped)
    return ped_id_counter + 1

# --- 初始化一些行人 ---
ped_id_counter = 1
ped_id_counter = spawn_pedestrian(ped_id_counter, "west", y_offset=-20)
ped_id_counter = spawn_pedestrian(ped_id_counter, "west", y_offset=20)
# ped_id_counter = spawn_pedestrian(ped_id_counter, "east") # 生成1个东侧行人

if pedestrians_list:
    selected_pedestrian_id = pedestrians_list[0].id


# --- 主仿真循环 ---
running = True
while running:
    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_s: # Spawn new pedestrian from West
                ped_id_counter = spawn_pedestrian(ped_id_counter, "west", y_offset=random.randint(-20, 20))
                if not selected_pedestrian_id and pedestrians_list: selected_pedestrian_id = pedestrians_list[-1].id
            if event.key == pygame.K_d: # Spawn new pedestrian from East
                ped_id_counter = spawn_pedestrian(ped_id_counter, "east", y_offset=random.randint(-20, 20))
                if not selected_pedestrian_id and pedestrians_list: selected_pedestrian_id = pedestrians_list[-1].id
            if event.key == pygame.K_b: # Selected pedestrian presses button
                if selected_pedestrian_id:
                    for p in pedestrians_list:
                        if p.id == selected_pedestrian_id:
                            p.is_requesting_button_press = not p.is_requesting_button_press
                            print(f"{p.id} button press: {p.is_requesting_button_press}")
                            break
            if event.key == pygame.K_m: # Toggle malicious for selected
                if selected_pedestrian_id:
                    for p in pedestrians_list:
                        if p.id == selected_pedestrian_id:
                            p.is_malicious = not p.is_malicious
                            print(f"{p.id} malicious: {p.is_malicious}")
                            break
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click to select pedestrian
                mouse_pos = event.pos
                for p in pedestrians_list:
                    dist_sq = (mouse_pos[0] - p.pos[0])**2 + (mouse_pos[1] - p.pos[1])**2
                    if dist_sq < (p.radius * 2)**2 : # Click near pedestrian
                        selected_pedestrian_id = p.id
                        break

    # --- 更新逻辑 ---
    for ped in pedestrians_list:
        ped.update()
        # 自动请求过马路
        if ped.is_at_wait_area and not ped.is_requesting_button_press:
            ped.is_requesting_button_press = True
            print(f"{ped.id} auto button press")

    rsu_unit.scan_and_process_pedestrians(pedestrians_list)
    rsu_request_priority = rsu_unit.determine_signal_request_priority()
    tlc_unit.update(rsu_request_priority)

    # Pedestrian crossing logic (simplified)
    if tlc_unit.pedestrian_phase == "walk":
        for ped in pedestrians_list:
            if ped.is_at_wait_area:
                # 移动到对面的等待区域 (强制在人行横道中心)
                target_y = H_CROSSWALK_RECT_NORTH.centery # 强制在人行横道中心
                if ped.target_wait_area_key == "WAIT_AREA_WEST":
                    ped.set_path_to_point((WAIT_AREA_EAST.left + PEDESTRIAN_RADIUS + 5, target_y))
                    ped.target_wait_area_key = "WAIT_AREA_EAST"
                else:
                    ped.set_path_to_point((WAIT_AREA_WEST.right - PEDESTRIAN_RADIUS - 5, target_y))
                    ped.target_wait_area_key = "WAIT_AREA_WEST"
                ped.is_requesting_button_press = False # 完成过马路后重置

    # --- 绘图 ---
    screen.fill(LIGHT_BLUE) # Light blue background

    # 绘制道路和人行横道
    pygame.draw.rect(screen, DARK_GREY, V_ROAD_RECT) # Main road

    # Draw crosswalk (multiple lines)
    crosswalk_line_width = 8
    crosswalk_spacing = 15
    num_lines = int(H_CROSSWALK_RECT_NORTH.width // (crosswalk_line_width + crosswalk_spacing))
    
    for i in range(num_lines):
        x = H_CROSSWALK_RECT_NORTH.left + i * (crosswalk_line_width + crosswalk_spacing)
        pygame.draw.rect(screen, WHITE, (x, H_CROSSWALK_RECT_NORTH.top, crosswalk_line_width, H_CROSSWALK_RECT_NORTH.height)) # 北
        pygame.draw.rect(screen, WHITE, (x, H_CROSSWALK_RECT_SOUTH.top, crosswalk_line_width, H_CROSSWALK_RECT_SOUTH.height)) # 南

    # Draw waiting area (schematic)
    pygame.draw.rect(screen, (230,230,250), WAIT_AREA_WEST) # Light purple
    pygame.draw.rect(screen, BLACK, WAIT_AREA_WEST,1)
    draw_text(screen, "W_Area", (WAIT_AREA_WEST.centerx, WAIT_AREA_WEST.top + 5), font_s, BLACK, center_aligned=True)
    pygame.draw.rect(screen, (230,250,230), WAIT_AREA_EAST) # Light green
    pygame.draw.rect(screen, BLACK, WAIT_AREA_EAST,1)
    draw_text(screen, "E_Area", (WAIT_AREA_EAST.centerx, WAIT_AREA_EAST.top + 5), font_s, BLACK, center_aligned=True)


    # Draw vehicle traffic lights (below road)
    v_light_base_x = V_ROAD_RECT.centerx
    v_light_base_y = V_ROAD_RECT.bottom + 140 # Below road (5cm = 100 pixels + 40)
    tlc_unit.draw(screen)

    # Draw RSU scanner (on sidewalk)
    rsu_scanner_radius = 7
    rsu_color = (50,50,150)
    draw_offset = 20
    pygame.draw.circle(screen, rsu_color, (V_ROAD_RECT.left - draw_offset, H_CROSSWALK_RECT_NORTH.centery), rsu_scanner_radius) # 西
    draw_text(screen, "W", (V_ROAD_RECT.left - draw_offset, H_CROSSWALK_RECT_NORTH.centery-15), font_s, rsu_color, center_aligned=True)
    pygame.draw.circle(screen, rsu_color, (V_ROAD_RECT.right + draw_offset, H_CROSSWALK_RECT_NORTH.centery),rsu_scanner_radius) # 东
    draw_text(screen, "E", (V_ROAD_RECT.right + draw_offset, H_CROSSWALK_RECT_NORTH.centery-15), font_s, rsu_color, center_aligned=True)
    pygame.draw.circle(screen, rsu_color, (V_ROAD_RECT.centerx, H_CROSSWALK_RECT_NORTH.top - draw_offset), rsu_scanner_radius) # 北
    draw_text(screen, "N", (V_ROAD_RECT.centerx, H_CROSSWALK_RECT_NORTH.top - draw_offset-15), font_s, rsu_color, center_aligned=True)
    pygame.draw.circle(screen,  rsu_color, (V_ROAD_RECT.centerx, H_CROSSWALK_RECT_SOUTH.bottom + draw_offset),rsu_scanner_radius) # 南
    draw_text(screen, "S", (V_ROAD_RECT.centerx, H_CROSSWALK_RECT_SOUTH.bottom + draw_offset-15), font_s,rsu_color, center_aligned=True)

    # 绘制行人
    for ped in pedestrians_list:
        ped_rsu_data = rsu_unit.pedestrian_tracking_data.get(ped.id)
        ped.draw(screen, ped_rsu_data)

    # 绘制车辆 (示例)
    vehicle_width = 30
    vehicle_height = 50
    vehicle_color = (128, 0, 128)  # 紫色
    vehicle_x = V_ROAD_RECT.centerx - vehicle_width // 2
    vehicle_y1 = V_ROAD_RECT.top + 50
    vehicle_y2 = V_ROAD_RECT.top + 150
    vehicle_y3 = V_ROAD_RECT.top + 250
    
    # 根据交通灯状态决定是否绘制车辆
    v_colors, _, _ = tlc_unit.get_signal_display_info()
    vehicle_speed = 2
    if v_colors["green"] == GREEN: # 绿灯
        vehicle_y1 += vehicle_speed # 车辆向下行驶
        if vehicle_y1 > SCREEN_HEIGHT:
            vehicle_y1 = V_ROAD_RECT.top + 50
        vehicle_y2 += vehicle_speed
        if vehicle_y2 > SCREEN_HEIGHT:
            vehicle_y2 = V_ROAD_RECT.top + 150
        vehicle_y3 += vehicle_speed
        if vehicle_y3 > SCREEN_HEIGHT:
            vehicle_y3 = V_ROAD_RECT.top + 250
    else: # 红灯或黄灯
        vehicle_y1 = V_ROAD_RECT.top + 50
        vehicle_y2 = V_ROAD_RECT.top + 150
        vehicle_y3 = V_ROAD_RECT.top + 250
        draw_text(screen, "GO", (vehicle_x + vehicle_width // 2, vehicle_y1 + vehicle_height // 2), font_m, WHITE, center_aligned=True) # 更改STOP颜色
    pygame.draw.rect(screen, vehicle_color, (vehicle_x, vehicle_y1, vehicle_width, vehicle_height), border_radius=5) # Draw stopped or moving vehicles
    pygame.draw.rect(screen, vehicle_color, (vehicle_x, vehicle_y2, vehicle_width, vehicle_height), border_radius=5)
    pygame.draw.rect(screen, vehicle_color, (vehicle_x, vehicle_y3, vehicle_width, vehicle_height), border_radius=5)

    # --- Draw debug info panel ---
    info_panel_x = 10
    info_panel_y = 10
    draw_text(screen, "PI-BREPSC Simulation", (info_panel_x, info_panel_y), font_m, BLACK)
    info_panel_y += 30
    draw_text(screen, f"Vehicle Light: {tlc_unit.vehicle_phase.upper()}", (info_panel_x, info_panel_y), font_s)
    info_panel_y += 20
    draw_text(screen, f"Pedestrian Light: {tlc_unit.pedestrian_phase.upper()}", (info_panel_x, info_panel_y), font_s)
    info_panel_y += 20
    if tlc_unit.is_pedestrian_request_servicing:
         draw_text(screen, "Servicing Pedestrian Request...", (info_panel_x, info_panel_y), font_s, ORANGE)
    info_panel_y += 20
    
    info_panel_y += 10 # 分隔

    if selected_pedestrian_id and selected_pedestrian_id in rsu_unit.pedestrian_tracking_data:
        data = rsu_unit.pedestrian_tracking_data[selected_pedestrian_id]
        ped_obj = next((p for p in pedestrians_list if p.id == selected_pedestrian_id), None)

        draw_text(screen, f"Selected Pedestrian: {selected_pedestrian_id}", (info_panel_x, info_panel_y), font_s, BLUE)
        info_panel_y += 20
        if ped_obj:
            draw_text(screen, f"  Position: ({int(ped_obj.pos[0])},{int(ped_obj.pos[1])})", (info_panel_x, info_panel_y), font_s)
            info_panel_y += 18
            draw_text(screen, f"  Motion State: {data['motion_state']}", (info_panel_x, info_panel_y), font_s)
            info_panel_y += 18
            draw_text(screen, f"  Button Pressed: {ped_obj.is_requesting_button_press}", (info_panel_x, info_panel_y), font_s)
            info_panel_y += 18
            draw_text(screen, f"  Is Malicious: {ped_obj.is_malicious}", (info_panel_x, info_panel_y), font_s)
            info_panel_y += 18

        draw_text(screen, f"  Avg RSSI: {data['avg_rssi_stable']:.1f} dBm (Std: {data['rssi_std_dev']:.1f})", (info_panel_x, info_panel_y), font_s)
        info_panel_y += 18
        draw_text(screen, f"  Is Anomalous: {data['is_anomalous']} ({data['anomaly_reason']})", (info_panel_x, info_panel_y), font_s, RED if data['is_anomalous'] else BLACK)
        info_panel_y += 18
        draw_text(screen, f"  Intent Prob: {data['intent_prob']:.2f}", (info_panel_x, info_panel_y), font_s, BLACK)
        info_panel_y += 18
        draw_text(screen, f"  Confidence: {data['confidence']:.2f}", (info_panel_x, info_panel_y), font_s, BLACK)
        info_panel_y += 18
        draw_text(screen, f"  High Conf Waiting: {data['time_waiting_high_conf_sec']:.1f}s", (info_panel_x, info_panel_y), font_s)
        info_panel_y += 25
        
        # 显示每个扫描仪的RSSI值
        draw_text(screen, "  Scanner RSSI:",(info_panel_x, info_panel_y), font_s)
        info_panel_y +=18
        for sc_id, rssi_hist in data["rssi_per_scanner"].items():
            if rssi_hist:
                draw_text(screen, f"    {sc_id}: {rssi_hist[-1]:.1f} dBm", (info_panel_x, info_panel_y), font_s)
            info_panel_y += 18

        draw_text(screen, "Controls: S/D=Spawn Ped, B=Button(Sel), M=Malicious(Sel),", (10, SCREEN_HEIGHT - 90), font_s, DARK_GREY)
        draw_text(screen, "Click=Select, ESC=Exit", (10, SCREEN_HEIGHT - 70), font_s, DARK_GREY)

    pygame.display.flip() # 更新整个屏幕
    clock.tick(FPS) # 控制帧率

pygame.quit()
sys.exit()