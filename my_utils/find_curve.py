import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


def func(X, a, b, c, d, e):
	x, y = X
	return a*x**2 + b*y**2 + c*x + d*y + e

def func2(x, a, b, c):
	return a*x**2 + b*x + c

def func3(X, a, b, c):
	x, y = X
	return a*x**2 + b*y**2 + c

def parabolic_surface(x, y, a, b, c, d, e):
    return a*x**2 + b*y**2 + c*x + d*y + e


data = np.load('./target_data/target_3d_coordinate.npz')

data_x = data['target_x']
data_y = data['target_y']
data_z = data['target_z']
video_name = str(data['video_name'])
interval = data['interval']
index_info = data['index_info']
target_num = data['target_num']
time = str(data['time']).split('.')[0]+' s'
info_detailed = '{}, {}, {}, {}'.format(interval,index_info, target_num, time)


data_x_show = data_x
data_y_show = data_y
data_z_show = data_z

remove_check_index = 0
for i in range(data_x.shape[0]):
	if data_x[i]>1900 :
		remove_check_index = i
		break

print('remove ', remove_check_index)

if remove_check_index > 10:
	for i in range(data_x.shape[0]-1, 1, -1):
		if i >= remove_check_index:
			print(i)
			data_z = np.delete(data_z, i)
			data_y = np.delete(data_y, i)
			data_x = np.delete(data_x, i)

lower_point_index = 0
for i in range(data_z.shape[0]-1):
	if data_z[i]<20 :
		lower_point_index = i
		break

if lower_point_index > 20:
	for i in range(data_x.shape[0]-1, 1, -1):
		if i >= lower_point_index:
			data_z = np.delete(data_z, i)
			data_y = np.delete(data_y, i)
			data_x = np.delete(data_x, i)

X = (data_x, data_y)

dot_num = data_x.shape[0]

distance = pow((pow((data_x[0]-data_x[dot_num-1]), 2) + pow((data_y[0]-data_y[dot_num-1]), 2)), 0.5)
print('distance : ', distance)

popt, pcov = curve_fit(func, X, data_z)

popt_h, pcov_h = curve_fit(func2, data_x, data_y)
popt_v, pcov_v = curve_fit(func2, data_x, data_z)
# print('3D params : ', popt)


a = popt[0]
b = popt[1]
c = popt[2]
d = popt[3]
e = popt[4]

a2 = popt_h[0]
b2 = popt_h[1]
c2 = popt_h[2]


# plotting the data points and the fitted curve
fig = plt.figure()
fig.set_figwidth(8)
fig.set_figheight(6)
ax = plt.axes(projection='3d')
plt.title(info_detailed)
plt.suptitle(video_name, fontsize=18)
ax.set_xlim(-50, 2000)
ax.set_ylim(-300, 300)
ax.set_zlim(0, 350)
ax.set_box_aspect([1,0.5,0.2])
ax.set_xlabel('x', fontsize=12)
ax.set_ylabel('y', fontsize=12)
ax.set_zlabel('z', fontsize=12)

# net point 
net_x = [1950, 1950, 1950, 1950, 1950]
net_y = [-100, 100, 100, -100, -100]
net_z = [0, 0, 170, 170, 0]
ax.plot(net_x, net_y, net_z, color='black', linewidth=2)

# nine-square
nine_x = [1950, 1950, 1950, 1950, 1950]
nine_y = [-25, 25, 25, -25, -25]
nine_z = [90, 90, 150, 150, 90]
ax.plot(nine_x, nine_y, nine_z, color='black', linewidth=1)

# base point 
ax.scatter3D(1844, 0, 0, marker='x')


ax.scatter3D(data_x_show, data_y_show, data_z_show, color='green')
# ax.scatter3D(data_x_show[:target_forward_num], data_y_show[:target_forward_num], data_z_show[:target_forward_num], color='green')
# ax.scatter3D(data_x_show[target_forward_num:], data_y_show[target_forward_num:], data_z_show[target_forward_num:], color='blue')


extend_start = int(data_x[0])+1
extend_x = []
extend_y = []

# if int(data_x[data_x.shape[0]-1]) < 1500:
# 	extend_start = int(data_x[data_x.shape[0]-1])

# for i in range(250, extend_start):
# 	extend_x.append(i)
# 	extend_y.append(a2*i*i + b2*i + c2)

# extend_x = np.array(extend_x)
# extend_y = np.array(extend_y)

# for i in range(len(extend_x)):
# 	extend_y[i] = a2*extend_x[i]*extend_x[i] + b2*extend_x[i] + c2
# x = np.linspace(0, 1900, 10000)
# y = np.linspace(-300, 300, 3000)
# x, y = np.meshgrid(x, y)
# z = parabolic_surface(x, y, a, b, c, d, e)  # 這裡使用示例的係數值
# ax.plot_surface(x, y, z, cmap='viridis')


ax.plot3D(data_x, a2*data_x**2 + b2*data_x + c2, a*(data_x**2)+b*(data_y**2)+c*data_x+d*data_y+e, color='red')
# ax.plot3D(extend_x, extend_y, a*(extend_x**2)+b*(extend_y**2)+c*extend_x+d*extend_y+e, color='orange', linewidth=3)

ax.invert_yaxis()
ax.scatter(0,0,0, color='black', marker='s')
ax.view_init(20, 120)
plt.savefig('curve.png')


save_name = video_name
print(save_name)
plt.savefig(video_name)

plt.show()




