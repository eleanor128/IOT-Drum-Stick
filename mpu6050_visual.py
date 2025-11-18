"""
MPU6050 3D Real-time Visualization
即時顯示 MPU6050 感測器的 3D 姿態
"""

import mpu6050
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time

class MPU6050Visualizer:
    """MPU6050 3D 視覺化類別"""
    
    def __init__(self, mpu_address=0x68):
        """初始化視覺化器"""
        # 初始化 MPU6050
        self.sensor = mpu6050.mpu6050(mpu_address)
        
        # 姿態角度（Roll, Pitch, Yaw）
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        
        # 互補濾波器參數
        self.alpha = 0.98  # 陀螺儀權重
        self.dt = 0.01     # 時間間隔（秒）
        
        # 初始化 Pygame 和 OpenGL
        pygame.init()
        self.display = (1200, 800)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption('MPU6050 3D Visualization - Drum Stick')
        
        # 設定 OpenGL 視角
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -10)
        
        # 啟用深度測試和光照
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # 設定光源
        glLight(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        glLight(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
        glLight(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
        
        # 字體設定
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def calculate_angles(self):
        """計算 Roll, Pitch, Yaw 角度（使用互補濾波器）"""
        # 讀取加速度計和陀螺儀數據
        accel = self.sensor.get_accel_data()
        gyro = self.sensor.get_gyro_data()
        
        # 從加速度計計算角度（度）
        accel_roll = math.atan2(accel['y'], accel['z']) * 180 / math.pi
        accel_pitch = math.atan2(-accel['x'], math.sqrt(accel['y']**2 + accel['z']**2)) * 180 / math.pi
        
        # 從陀螺儀積分角度
        gyro_roll = self.roll + gyro['x'] * self.dt
        gyro_pitch = self.pitch + gyro['y'] * self.dt
        gyro_yaw = self.yaw + gyro['z'] * self.dt
        
        # 互補濾波器融合
        self.roll = self.alpha * gyro_roll + (1 - self.alpha) * accel_roll
        self.pitch = self.alpha * gyro_pitch + (1 - self.alpha) * accel_pitch
        self.yaw = gyro_yaw  # Yaw 只能用陀螺儀
        
        return accel, gyro
    
    def draw_cube(self):
        """繪製立方體（代表感測器）"""
        vertices = [
            [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1],  # 後面
            [1, -1, 1], [1, 1, 1], [-1, -1, 1], [-1, 1, 1]       # 前面
        ]
        
        edges = [
            (0,1), (1,2), (2,3), (3,0),  # 後面
            (4,5), (5,7), (7,6), (6,4),  # 前面
            (0,4), (1,5), (2,7), (3,6)   # 連接線
        ]
        
        faces = [
            (0,1,2,3), (4,5,7,6),  # 前後
            (0,4,5,1), (2,3,6,7),  # 左右
            (0,3,6,4), (1,2,7,5)   # 上下
        ]
        
        colors = [
            (1, 0, 0), (0, 1, 0),    # 紅、綠
            (0, 0, 1), (1, 1, 0),    # 藍、黃
            (1, 0, 1), (0, 1, 1)     # 洋紅、青
        ]
        
        # 繪製面
        glBegin(GL_QUADS)
        for i, face in enumerate(faces):
            glColor3fv(colors[i])
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        # 繪製邊框
        glDisable(GL_LIGHTING)
        glColor3f(0, 0, 0)
        glLineWidth(2)
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
        glEnable(GL_LIGHTING)
    
    def draw_axes(self):
        """繪製座標軸"""
        glDisable(GL_LIGHTING)
        glLineWidth(3)
        glBegin(GL_LINES)
        
        # X 軸 (紅)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(3, 0, 0)
        
        # Y 軸 (綠)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 3, 0)
        
        # Z 軸 (藍)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 3)
        
        glEnd()
        glEnable(GL_LIGHTING)
    
    def draw_text_2d(self, text, position, color=(255, 255, 255), font=None):
        """在 2D 位置繪製文字"""
        if font is None:
            font = self.font
        
        text_surface = font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glRasterPos2f(position[0], position[1])
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def run(self):
        """主迴圈"""
        clock = pygame.time.Clock()
        rotation_speed = 1.0
        
        print("=" * 50)
        print("MPU6050 3D Visualization")
        print("=" * 50)
        print("\n控制說明:")
        print("  - 滑鼠拖曳: 旋轉視角")
        print("  - 滾輪: 縮放")
        print("  - R 鍵: 重置姿態")
        print("  - ESC 或關閉視窗: 退出")
        print("\n")
        
        mouse_down = False
        mouse_x, mouse_y = 0, 0
        view_rotation_x, view_rotation_y = 0, 0
        
        running = True
        while running:
            # 處理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        # 重置姿態
                        self.roll = 0
                        self.pitch = 0
                        self.yaw = 0
                        print("姿態已重置")
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左鍵
                        mouse_down = True
                        mouse_x, mouse_y = event.pos
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        mouse_down = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if mouse_down:
                        dx = event.pos[0] - mouse_x
                        dy = event.pos[1] - mouse_y
                        view_rotation_y += dx * 0.5
                        view_rotation_x += dy * 0.5
                        mouse_x, mouse_y = event.pos
            
            # 計算角度
            accel, gyro = self.calculate_angles()
            
            # 清除畫面
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # 保存當前矩陣
            glPushMatrix()
            
            # 套用視角旋轉
            glRotatef(view_rotation_x, 1, 0, 0)
            glRotatef(view_rotation_y, 0, 1, 0)
            
            # 繪製座標軸
            self.draw_axes()
            
            # 套用感測器姿態
            glRotatef(-self.pitch, 1, 0, 0)  # Pitch (X軸)
            glRotatef(-self.roll, 0, 0, 1)   # Roll (Z軸)
            glRotatef(self.yaw, 0, 1, 0)     # Yaw (Y軸)
            
            # 繪製立方體
            self.draw_cube()
            
            # 恢復矩陣
            glPopMatrix()
            
            # 顯示數據（2D 文字）
            y_offset = 30
            self.draw_text_2d("MPU6050 3D Visualization", (10, y_offset), (255, 255, 0))
            
            y_offset += 50
            self.draw_text_2d(f"Roll:  {self.roll:7.2f}°", (10, y_offset), (255, 100, 100), self.small_font)
            
            y_offset += 30
            self.draw_text_2d(f"Pitch: {self.pitch:7.2f}°", (10, y_offset), (100, 255, 100), self.small_font)
            
            y_offset += 30
            self.draw_text_2d(f"Yaw:   {self.yaw:7.2f}°", (10, y_offset), (100, 100, 255), self.small_font)
            
            y_offset += 50
            self.draw_text_2d("Accelerometer:", (10, y_offset), (200, 200, 200), self.small_font)
            
            y_offset += 25
            self.draw_text_2d(f"  X: {accel['x']:6.2f}g  Y: {accel['y']:6.2f}g  Z: {accel['z']:6.2f}g", 
                            (10, y_offset), (180, 180, 180), self.small_font)
            
            y_offset += 35
            self.draw_text_2d("Gyroscope:", (10, y_offset), (200, 200, 200), self.small_font)
            
            y_offset += 25
            self.draw_text_2d(f"  X: {gyro['x']:6.1f}°/s  Y: {gyro['y']:6.1f}°/s  Z: {gyro['z']:6.1f}°/s", 
                            (10, y_offset), (180, 180, 180), self.small_font)
            
            # 更新顯示
            pygame.display.flip()
            clock.tick(100)  # 100 FPS
        
        pygame.quit()
        print("\n視覺化已結束")


def main():
    """主程式"""
    try:
        print("正在初始化 MPU6050...")
        visualizer = MPU6050Visualizer()
        print("初始化完成！啟動視覺化...\n")
        visualizer.run()
    
    except KeyboardInterrupt:
        print("\n\n程式被使用者中斷")
    
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
