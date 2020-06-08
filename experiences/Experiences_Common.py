import pickle
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from cqapk_to_datalog.data_structures import Database

class TestDatabase(Database):
    def __init__(self, relations, n_facts):
        Database.__init__(self)
        self.blocks = {}
        for relation, arity in relations:
            self.add_relation(relation, arity)
            self.blocks[relation] = {}

def clear():
    os.system('cls')

def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

def plot_3D(file, x_axis, y_axis, z_axis, title):
    data_file = load_obj(file)
    min_x = min(x for x,y in data_file)
    max_x = max(x for x,y in data_file)
    min_y = min(y for x,y in data_file)
    max_y = max(y for x,y in data_file)
    min_z = min(data_file[k] for k in data_file)
    max_z = max(data_file[k] for k in data_file)
    #x = np.arange(min_x, max_x + 1)
    x = np.array([x for x,y in data_file])
    #y = np.arange(min_y, max_y + 1)
    y = np.array([y for x,y in data_file])
    print(x)
    print(y)
    print(len(x))
    print(len(y))
    X, Y = np.meshgrid(x, y)
    z_image = np.apply_along_axis(lambda _: data_file[(_[0], _[1])], 2, np.dstack([X,Y]))
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(X, Y, z_image, rstride=1, cstride=1,cmap=mpl.cm.coolwarm,vmin=0, vmax=max_z)
    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)
    ax.set_zlabel(z_axis)
    ax.set_title(title)
    ax.view_init(ax.elev, -120)
    fig.colorbar(surf)
    plt.show()

def plot_2D(x, y, x_axis, y_axis, title):
    plt.plot(x, y)
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.show()