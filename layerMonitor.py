

from qgis.core import QgsProject,QgsSpatialIndex,QgsMapLayer,QgsVectorLayer
from qgis.PyQt.QtCore import QTimer

import sys,os
debuger_path = os.path.join(os.path.dirname(__file__),'pydevd-pycharm.egg')
print(debuger_path)
sys.path.append(debuger_path)

import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=53001, stdoutToServer=True, stderrToServer=True)  # 开启调试




spatial_index = {}  # 全局索引对象



import time,math
from functools import wraps
def run_timer(func):
    @wraps(func)  # 保留原函数元数据:ml-citation{ref="3,4" data="citationList"}
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 执行时间: {end - start:.4f}秒")
        return result
    return wrapper







class LayerMonitor:
    def __init__(self):
        self.handled_layers = set()  # 记录已处理图层ID
        # 项目打开时触发已有图层检查 , 临时图层删除, 非临时矢量图层 添加索引对象
        # QgsProject.instance().readProject.connect(self.init_existing_layers)
        # 新图层添加时触发检查  非临时矢量图层 添加索引对象
        QgsProject.instance().layersAdded.connect(self.on_layers_added)
        # 移除图层时触发检查   删除图层的 索引对象
        QgsProject.instance().layersRemoved.connect(self.on_layers_removed)

        # 项目打开时触发 转换为内存图层
        # self.on_load_trans_layer()


    @run_timer
    def on_load_trans_layer(self):
        all_layers = QgsProject.instance().mapLayers().values()
        for layer in all_layers:
            if self.is_persistent_layer(layer):
                if isinstance(layer, QgsVectorLayer):
                    convert_to_memory_layer(layer)      # 转换为内存图层



    def init_existing_layers(self):
        global spatial_index
        # 处理项目文件中的现有非临时图层
        for layer in QgsProject.instance().mapLayers().values():
            print("项目打开时触发,矢量图层添加索引对象:", layer.name())


    def is_persistent_layer(self,layer):
        # 排除内存图层（临时图层）
        if layer.dataProvider().name() == 'memory':
            return False
        # 检查数据源是否包含临时路径标识（如/tmp/）
        if '/tmp/' in layer.source().lower():
            return False
        return True


    def on_layers_added(self, layers):          # 新图层添加时触发检查  非临时矢量图层 添加索引对象
        global spatial_index
        for layer in layers:
            if self.is_persistent_layer(layer):
                self.on_load_trans_layer()        # 触发 转换为内存图层


        layers = QgsProject.instance().mapLayers().values()

        # 处理动态添加的图层
        for layer in layers:
            if layer.id() not in self.handled_layers:
            # if layer.id() not in self.handled_layers:
                self.trigger_post_load_action(layer)  # 延迟500毫秒等待图层加载完成
                if layer.type() == QgsMapLayer.LayerType.VectorLayer:  # 矢量图层
                    spatial_index[layer.id()] = QgsSpatialIndex(layer.getFeatures())  #  添加索引对象
                    print("新图层添加时触发检查,矢量图层添加索引对象:", layer.name())


    def on_layers_removed(self, layers):          # 新图层添加时触发检查  非临时矢量图层 添加索引对象
        global spatial_index
        # 处理动态移除的图层
        for layer in layers:
            try:
                if type(layer)==str:
                    layer_id = layer
                elif type(layer)==QgsMapLayer:
                    layer_id = layer.id()

                if layer_id in spatial_index.keys():
                    del spatial_index[layer_id]
                    print("删除矢量图层索引对象:", layer_id)
            except Exception as e:
                print(e)


    def trigger_post_load_action(self, layer):
        # 标记为已处理
        self.handled_layers.add(layer.id())
        # 延迟500ms确保要素加载完成
        QTimer.singleShot(500, lambda: self.execute_layer_logic(layer))


    def execute_layer_logic(self, layer):
        print("延迟500ms确保要素加载完成:", layer)




# 将图层转换为内存 的临时草图 来提高运行速度
def convert_to_memory_layer(input_layer):
    """
    将输入矢量图层转换为内存图层并替换原图层
    参数：
        input_layer: QgsVectorLayer对象
    返回：
        生成的内存图层对象
    """
    from qgis.core import QgsProject, QgsVectorLayer

    # 获取源图层属性
    crs = input_layer.crs().authid()
    geom_type = input_layer.geometryType()
    fields = input_layer.fields()

    # 根据几何类型创建对应内存图层
    type_map = {
        0: "Point",
        1: "LineString",
        2: "Polygon",
        3: "MultiPoint",
        4: "MultiLineString",
        5: "MultiPolygon"
    }
    uri = f"{type_map.get(geom_type, 'Point')}?crs={crs}"
    mem_layer = QgsVectorLayer(uri, f"{input_layer.name()}_memory", "memory")

    # 复制字段结构
    provider = mem_layer.dataProvider()
    provider.addAttributes(fields.toList())
    mem_layer.updateFields()

    # 复制所有要素
    features = [feat for feat in input_layer.getFeatures()]
    provider.addFeatures(features)
    mem_layer.updateExtents()

    # 图层管理操作
    project = QgsProject.instance()
    project.addMapLayer(mem_layer, False)  # 不自动添加到图例
    layer_tree = project.layerTreeRoot()
    layer_tree.insertLayer(0, mem_layer)  # 插入到图层树顶部

    print(f"图层{input_layer.name()}转换为内存图层{mem_layer.name()}")

    # 移除原图层
    project.removeMapLayer(input_layer)

    return mem_layer


