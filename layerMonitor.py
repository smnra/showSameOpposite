

from qgis.core import QgsProject,QgsSpatialIndex,QgsMapLayer
from qgis.PyQt.QtCore import QTimer


spatial_index = {}  # 全局索引对象






class LayerMonitor:
    def __init__(self):
        self.handled_layers = set()  # 记录已处理图层ID
        # 项目打开时触发已有图层检查 , 临时图层删除, 非临时矢量图层 添加索引对象
        # QgsProject.instance().readProject.connect(self.init_existing_layers)
        # 新图层添加时触发检查  非临时矢量图层 添加索引对象
        QgsProject.instance().layersAdded.connect(self.on_layers_added)
        # 移除图层时触发检查   删除图层的 索引对象
        QgsProject.instance().layersRemoved.connect(self.on_layers_removed)



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
        # 处理动态添加的图层
        for layer in layers:
            if self.is_persistent_layer(layer) and layer.id() not in self.handled_layers:
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