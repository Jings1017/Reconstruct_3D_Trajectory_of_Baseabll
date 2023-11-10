import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from trendup_video.type_alias import Frame

from src.objects import TrajPosition, TrajCalculateResult, TrajCalculateMaterials, CurveFunctionParameters, \
    GetYFunctionParameters, GetXFromTimeFunctionParameters


class FindFittingCurve:
    def __init__(self, img_save_dir: str):
        self.img_save_dir = img_save_dir

        self.target_x = np.zeros(1)
        self.target_y = np.zeros(1)
        self.target_z = np.zeros(1)
        self.target_timestamp = np.zeros(1)

        self.shortest_distance = 0
        self.flight_timestamp = 0
        self.is_strike = False
        self.is_land_early = False
        self.land_index = 0
        self.land_x = 0

        self.fig = plt.figure()
        self.fig.set_size_inches(8, 6)
        self.ax3d = self.fig.add_subplot(projection='3d')

        self.fit_curve_coef = np.zeros(5)
        self.y_coef = np.zeros(3)
        self.x_coef = np.zeros(2)

        self.exist_front_ball = True
        self.exist_back_ball = True

        self.curve_min_timestamp = 0
        self.curve_max_timestamp = 0

        self.release_traj_position = TrajPosition(x=0, y=0, z=0, timestamp=0)
        self.home_plate_traj_position = TrajPosition(x=0, y=0, z=0, timestamp=0)

    def load_data(self, traj_positions: list[TrajPosition]):
        num_of_targets = len(traj_positions)
        self.target_x = np.resize(self.target_x, num_of_targets)
        self.target_y = np.resize(self.target_y, num_of_targets)
        self.target_z = np.resize(self.target_z, num_of_targets)
        self.target_timestamp = np.resize(self.target_timestamp, num_of_targets)

        for i in range(num_of_targets):
            self.target_x[i] = traj_positions[i].x
            self.target_y[i] = traj_positions[i].y
            self.target_z[i] = traj_positions[i].z
            self.target_timestamp[i] = traj_positions[i].timestamp
            # print('%d %d %7.2f %6.2f %6.2f' % (
            #     i, self.target_timestamp[i], self.target_x[i], self.target_y[i], self.target_z[i]))

    def remove_hitting_net_ball(self, mound_distance):
        remove_check_index = 0
        for i in range(self.target_x.shape[0]):
            if self.target_x[i] > mound_distance + 50:
                remove_check_index = i
                break
        if remove_check_index > 8:
            for i in reversed(range(self.target_x.shape[0])):
                if i >= remove_check_index:
                    print(f'-- remove {self.target_x[i]}, reason : out of zone')
                    self.delete_data(i)

    def remove_negative_ball(self):
        negative_index_list = []
        for i in range(self.target_x.shape[0]):
            if self.target_x[i] < 140 or self.target_x[i]>1900:
                negative_index_list.append(i)
        for i in reversed(range(len(negative_index_list))):
            print(f'-- remove {self.target_x[negative_index_list[i]]}, reason : negative ball')
            self.delete_data(negative_index_list[i])

    def remove_abnormal_ball(self):
        unsort_index_list = []
        for i in range(self.target_x.shape[0]-1):
            if self.target_x[i]>self.target_x[i+1]:
                unsort_index_list.append(i)
        for i in reversed(range(len(unsort_index_list))):
            print(f'-- remove {self.target_x[unsort_index_list[i]]}, reason : unsorting ball')
            self.delete_data(unsort_index_list[i])

    def early_land_process(self):
        for i in range(self.target_z.shape[0]):
            if self.target_z[i] < 20 and self.target_x[i] < 1800:
                self.is_land_early = True
                self.land_index = i
                self.land_x = self.target_x[i]
        if self.is_land_early:
            for i in reversed(range(self.target_x.shape[0])):
                if i > self.land_index:
                    print(f'-- remove {self.target_x[i]}, reason : land early')
                    self.delete_data(i)

    def find_Z_coef(self, X: (float, float), a: float, b: float, c: float, d: float, e: float) -> float:
        x, y = X
        return a * x ** 2 + b * y ** 2 + c * x + d * y + e

    def find_Y_coef(self, x: float, a: float, b: float, c: float) -> float:
        return a * x ** 2 + b * x + c

    def find_X_coef(self, x: float, a: float, b: float) -> float:
        return a * x + b

    def get_Y_by_X(self, x: float) -> float:
        return self.y_coef[0] * x ** 2 + self.y_coef[1] * x + self.y_coef[2]

    def get_Z_by_XY(self, x: float, y: float) -> float:
        return self.fit_curve_coef[0] * x ** 2 + self.fit_curve_coef[1] * y ** 2 + self.fit_curve_coef[2] * x + \
            self.fit_curve_coef[3] * y + self.fit_curve_coef[4]

    def get_X_by_time(self, t: float) -> float:
        return self.x_coef[0] * t + self.x_coef[1]

    def get_time_by_X(self, x: float) -> float:
        return (x - self.x_coef[1]) / self.x_coef[0]

    def print_raw_data(self):
        print(f'------- CURVE DATA -------')
        for i in range(self.target_x.shape[0]):
            print(f'{i:02d} {self.target_timestamp[i]}  {self.target_x[i]:7.2f}  {self.target_y[i]:7.2f}  {self.target_z[i]:7.2f}')


    def draw_env(self, materials: TrajCalculateMaterials):
        # net point 
        # net_x = [1950, 1950, 1950, 1950, 1950]
        # net_y = [-100, 100, 100, -100, -100]
        # net_z = [0, 0, 170, 170, 0]
        # self.ax3d.plot(net_x, net_y, net_z, color='black', linewidth=2)

        # nine-square
        # nine_x = [1950, 1950, 1950, 1950, 1950]
        # nine_y = [-25, 25, 25, -25, -25]
        # nine_z = [90, 90, 150, 150, 90]
        # self.ax3d.plot(nine_x, nine_y, nine_z, color='black', linewidth=1)

        # pitch point 
        pitch_x = [0, 0, -15, -15, 0]
        pitch_y = [30, -30, -30, 30, 30]
        pitch_z = [0, 0, 0, 0, 0]
        self.ax3d.plot(pitch_x, pitch_y, pitch_z, color='black', linewidth=1)

        home_plate_x = [materials.mound_distance_cm, materials.mound_distance_cm, materials.mound_distance_cm + 22, \
                        materials.mound_distance_cm + 43, materials.mound_distance_cm + 22, materials.mound_distance_cm]
        home_plate_y = [-22, 22, 22, 0, -22, -22]
        home_plate_z = [0, 0, 0, 0, 0, 0]
        self.ax3d.plot(home_plate_x, home_plate_y, home_plate_z, color='black', linewidth=1)

        strike_center_x = materials.mound_distance_cm + 21.5
        strike_center_z = (materials.strike_zone.low_cm + materials.strike_zone.high_cm) / 2
        self.ax3d.scatter3D(strike_center_x, 0, strike_center_z, marker='.', color='red')
        strike_zone_bottom_z = [materials.strike_zone.low_cm] * 6
        self.ax3d.plot(home_plate_x, home_plate_y, strike_zone_bottom_z, color='blue', linewidth=1)
        strike_zone_top_z = [materials.strike_zone.high_cm] * 6
        self.ax3d.plot(home_plate_x, home_plate_y, strike_zone_top_z, color='blue', linewidth=1)

        for i in range(6):
            self.ax3d.plot([home_plate_x[i], home_plate_x[i]], [home_plate_y[i], home_plate_y[i]],
                           [strike_zone_bottom_z[i], strike_zone_top_z[i]], color='blue', linewidth=1)

    def plot_setting(self, materials: TrajCalculateMaterials):
        self.ax3d.set_xlim(-50, 2000)
        self.ax3d.set_ylim(-300, 300)
        self.ax3d.set_zlim(0, 350)
        self.ax3d.set_box_aspect([1, 0.5, 0.2])
        self.ax3d.set_xlabel('x', fontsize=7)
        self.ax3d.set_ylabel('y', fontsize=7)
        self.ax3d.set_zlabel('z', fontsize=7)
        self.ax3d.tick_params(axis='x', labelsize=7)
        self.ax3d.tick_params(axis='y', labelsize=7)
        self.ax3d.tick_params(axis='z', labelsize=7)
        self.ax3d.invert_yaxis()
        self.draw_env(materials)
        self.ax3d.view_init(10, 130)
        # self.ax3d.text(1900, 100, -800, 'Pitching Trajectory', fontsize=20)
        # self.ax3d.scatter3D(data_x_show, data_y_show, data_z_show, color='violet')

    def draw_curve_on_plot(self, target_x: float, release_x: float, materials: TrajCalculateMaterials,
                           release_time: float):
        # generate 300 points between pitcher and zone
        release_x = max(release_x, 120)
        print(f'------- RELEASE X -------')
        print('release x : ', release_x)
        curve_start_x = release_x
        curve_end_x = materials.mound_distance_cm
        self.curve_max_timestamp = self.get_time_by_X(materials.mound_distance_cm)

        if self.is_land_early or not self.exist_back_ball:
            self.curve_max_timestamp = self.target_timestamp[-1] - release_time
            curve_end_x = target_x[-1]

        if not self.exist_front_ball:
            self.curve_min_timestamp = self.target_timestamp[0] - release_time
            curve_start_x = target_x[0]

        self.release_traj_position.x = curve_start_x
        self.release_traj_position.y = self.get_Y_by_X(self.release_traj_position.x)
        self.release_traj_position.z = self.get_Z_by_XY(self.release_traj_position.x,self.release_traj_position.y)
        self.release_traj_position.timestamp = self.get_time_by_X(self.release_traj_position.x)

        curve_length = int(curve_end_x - curve_start_x)

        # print('curve min time : ', self.curve_min_timestamp)
        # print('curve max time : ', self.curve_max_timestamp)

        gen_interval = curve_length / 300
        gen_x, gen_y, gen_z = [], [], []
        for g in range(300):
            sub_x = curve_start_x + gen_interval * g
            sub_y = self.get_Y_by_X(sub_x)
            sub_z = self.get_Z_by_XY(sub_x, sub_y)
            if sub_z>25:
                gen_x.append(sub_x)
                gen_y.append(sub_y)
                gen_z.append(sub_z)
            else:
                break
        gen_x = np.array(gen_x)
        gen_y = np.array(gen_y)
        gen_z = np.array(gen_z)

        cmap = plt.get_cmap('autumn')
        c = np.linspace(0, 1, gen_x.shape[0])
        self.ax3d.scatter3D(gen_x, gen_y, gen_z, c=c, cmap=cmap)

    def turn_to_numpy_arr(self, fig) -> Frame:
        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        return frame

    def get_release_traj_position(self, release_time: float):
        # t_release -> x -> y -> z (release height) 
        self.release_traj_position.x = self.get_X_by_time(0)
        self.release_traj_position.y = self.get_Y_by_X(self.release_traj_position.x)
        self.release_traj_position.z = self.get_Z_by_XY(self.release_traj_position.x, self.release_traj_position.y)
        self.release_traj_position.timestamp = release_time

    def get_home_plate_traj_position(self, mound_distance: float):
        self.home_plate_traj_position.x = mound_distance
        self.home_plate_traj_position.y = self.get_Y_by_X(mound_distance)
        self.home_plate_traj_position.z = self.get_Z_by_XY(mound_distance, self.home_plate_traj_position.y)
        self.home_plate_traj_position.timestamp = self.get_time_by_X(mound_distance)

    def get_flight_timestamp(self, mound_distance: float):
        self.flight_timestamp = self.get_time_by_X(mound_distance)
        if self.is_land_early:
            self.flight_timestamp = self.get_time_by_X(self.land_x)
        # print('flight time : {:.2f} ms'.format(self.flight_timestamp))

    def cal_shortest_distance_from_strike_center(self, materials: TrajCalculateMaterials):
        # cal minimal distance
        strike_center_x = materials.mound_distance_cm + 22.25
        strike_center_y = 0
        strike_center_z = (materials.strike_zone.high_cm + materials.strike_zone.low_cm) / 2
        strike_center = np.array([strike_center_x, strike_center_y, strike_center_z])

        closest_x = strike_center_x
        if self.is_land_early:
            closest_x = self.land_x
        closest_y = self.get_Y_by_X(closest_x)
        closest_z = self.get_Z_by_XY(closest_x, closest_y)
        closest_point = np.array([closest_x, closest_y, closest_z])
        self.shortest_distance = np.linalg.norm(closest_point - strike_center)
        self.shortest_distance = format(self.shortest_distance * 0.01, '.3f')
        # print("shortest distance : {} m".format(self.shortest_distance))

    def delete_data(self, i):
        self.target_x = np.delete(self.target_x, i)
        self.target_y = np.delete(self.target_y, i)
        self.target_z = np.delete(self.target_z, i)
        self.target_timestamp = np.delete(self.target_timestamp, i)

    def get_fitting_curve_data(self, traj_positions: list[TrajPosition], release_time: float,
                               materials: TrajCalculateMaterials, exist_front_ball: bool,
                               exist_back_ball: bool) -> TrajCalculateResult:

        # data_x_show, data_y_show, data_z_show = target_x, target_y, target_z
        self.load_data(traj_positions)

        self.exist_front_ball = exist_front_ball
        self.exist_back_ball = exist_back_ball
        print(f'------- EXIST BALL -------')
        print(f'exist balls in pitch : {self.exist_front_ball}')
        print(f'exist balls in zone : {self.exist_back_ball}')

        original_x = self.target_x.copy()
        original_y = self.target_y.copy()
        original_z = self.target_z.copy()

        print(f'------- REMOVE BALL -------')
        self.remove_negative_ball()
        self.remove_hitting_net_ball(materials.mound_distance_cm)
        self.remove_abnormal_ball()
        self.early_land_process()
        
        if self.target_x.shape[0]<5:
            return None
        
        self.print_raw_data()

        # xy -> z
        self.fit_curve_coef, pcov = curve_fit(self.find_Z_coef, (self.target_x, self.target_y), self.target_z)
        # x -> y
        self.y_coef, pcov_h = curve_fit(self.find_Y_coef, self.target_x, self.target_y)
        # t-> x
        self.x_coef, pcov_t = curve_fit(self.find_X_coef, self.target_timestamp - release_time, self.target_x)

        # self.get_release_traj_position(release_time)

        # front edge of the strike zone 
        self.get_home_plate_traj_position(materials.mound_distance_cm)

        # check is strike or not 
        if self.home_plate_traj_position.y < 22 \
                and self.home_plate_traj_position.y > -22 \
                and self.home_plate_traj_position.z >= materials.strike_zone.low_cm \
                and self.home_plate_traj_position.z <= materials.strike_zone.high_cm:
            self.is_strike = True

        self.get_flight_timestamp(materials.mound_distance_cm)
        self.cal_shortest_distance_from_strike_center(materials)
        self.plot_setting(materials)
        self.draw_curve_on_plot(self.target_x, self.release_traj_position.x, materials, release_time)
        self.ax3d.scatter3D(original_x, original_y, original_z, color='black', marker='o')

        # plt.show()

        result = TrajCalculateResult(
            is_strike=self.is_strike,
            is_land_early=self.is_land_early,
            distance_from_center=self.shortest_distance,
            position_on_home_plate=self.home_plate_traj_position,
            curve_function=CurveFunctionParameters(
                a=self.fit_curve_coef[0],
                b=self.fit_curve_coef[1],
                c=self.fit_curve_coef[2],
                d=self.fit_curve_coef[3],
                e=self.fit_curve_coef[4]
            ),
            get_y_function=GetYFunctionParameters(
                a=self.y_coef[0],
                b=self.y_coef[1],
                c=self.y_coef[2],
            ),
            get_x_from_time_function=GetXFromTimeFunctionParameters(
                a=self.x_coef[0],
                b=self.x_coef[1],
            ),
            full_curve_img=self.turn_to_numpy_arr(self.fig),
            release_height=self.release_traj_position.z,
            flight_duration_of_millis=int(self.flight_timestamp),
            release_timestamp=int(release_time),
            release_extension=self.release_traj_position.x,
            curve_min_timestamp=int(self.curve_min_timestamp),
            curve_max_timestamp=int(self.curve_max_timestamp),
        )

        return result
