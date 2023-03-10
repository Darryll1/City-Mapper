import folium, io, json, sys, math, random, os
import psycopg2
from folium.plugins import Draw, MousePosition, MeasureControl
from jinja2 import Template
from branca.element import Element
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(600, 600)
	
        main = QWidget()
        self.setCentralWidget(main)
        main.setLayout(QVBoxLayout())
        main.setFocusPolicy(Qt.StrongFocus)

        self.tableWidget = QTableWidget()
        self.tableWidget.doubleClicked.connect(self.table_Click)
        self.rows = []

        self.webView = myWebView()
		
        controls_panel = QHBoxLayout()
        mysplit = QSplitter(Qt.Vertical)
        mysplit.addWidget(self.tableWidget)
        mysplit.addWidget(self.webView)

        main.layout().addLayout(controls_panel)
        main.layout().addWidget(mysplit)

        _label = QLabel('From: ', self)
        _label.setFixedSize(30,20)
        self.from_box = QComboBox() 
        self.from_box.setEditable(True)
        self.from_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.from_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.from_box)

        _label = QLabel('  To: ', self)
        _label.setFixedSize(20,20)
        self.to_box = QComboBox() 
        self.to_box.setEditable(True)
        self.to_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.to_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.to_box)

        _label = QLabel('Hops: ', self)
        _label.setFixedSize(20,20)
        self.hop_box = QComboBox() 
        self.hop_box.addItems( ['1', '2', '3', '4'] )
        self.hop_box.setCurrentIndex( 2 )
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.hop_box)

        self.go_button = QPushButton("Go!")
        self.go_button.clicked.connect(self.button_Go)
        controls_panel.addWidget(self.go_button)
           
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.button_Clear)
        controls_panel.addWidget(self.clear_button)

        self.maptype_box = QComboBox()
        self.maptype_box.addItems(self.webView.maptypes)
        self.maptype_box.currentIndexChanged.connect(self.webView.setMap)
        controls_panel.addWidget(self.maptype_box)
           
        self.connect_DB()

        self.startingpoint = True
                   
        self.show()
        

    def connect_DB(self):
        self.conn = psycopg2.connect(database="ProjetBDD", user="DarYanJer", host="localhost", password="projet")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""SELECT distinct name FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i ORDER BY name""")
        self.conn.commit()
        rows = self.cursor.fetchall()

        for row in rows : 
            self.from_box.addItem(str(row[0]))
            self.to_box.addItem(str(row[0]))


    def table_Click(self):
        k = 0
        prev_lat = 0
        for col in self.rows[self.tableWidget.currentRow()] :
            if (k % 3) == 0:
                lst = col.split(',')
                lat = float(lst[0])
                lon = float(lst[1]) 

                if prev_lat != 0:
                    self.webView.addSegment( prev_lat, prev_lon, lat, lon )
                prev_lat = lat
                prev_lon = lon

                self.webView.addMarker( lat, lon )
            k = k + 1
        

    def button_Go(self):
        self.tableWidget.clearContents()

        _fromstation = str(self.from_box.currentText())
        _tostation = str(self.to_box.currentText())
        _hops = int(self.hop_box.currentText())

        self.rows = []

        
            
        if _hops >= 1 :
            self.cursor.execute(""f" SELECT distinct A.name, A.route_name, B.name FROM (SELECT * FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i  AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS A, (SELECT * FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.to_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS B WHERE A.name= $${_fromstation}$$ AND B.name= $${_tostation}$$ AND A.route_i_counts = B.route_i_counts""")
            self.conn.commit()
            self.rows += self.cursor.fetchall()

        if _hops >= 2 : 
            self.cursor.execute(""f" SELECT distinct A.name, A.route_name, B.name, C.route_name,D.name FROM (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS A,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS B, (SELECT * FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i  AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS C,(SELECT * FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.to_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts ) AS D WHERE A.name = $${_fromstation}$$  AND D.name = $${_tostation}$$ AND A.route_i_counts = B.route_i_counts AND B.name = C.name  AND C.route_i_counts = D.route_i_counts AND A.route_i_counts <> C.route_i_counts  AND A.name <> B.name   AND B.name <> D.name""")
            self.conn.commit()
            self.rows += self.cursor.fetchall()

        if _hops >= 3 : 
            self.cursor.execute(""f" SELECT distinct A.name, A.route_name, B2.name, B2.route_name, C2.name, C2.route_name, D.name FROM (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS A, (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS B1,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS B2,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS C1, (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS C2, (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.to_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS D WHERE A.name = $${_fromstation}$$ AND A.route_i_counts = B1.route_i_counts AND B1.name = B2.name AND B2.route_i_counts = C1.route_i_counts AND C1.name = C2.name AND C2.route_i_counts = D.route_i_counts AND D.name = $${_tostation}$$ AND A.route_i_counts <> B2.route_i_counts AND B2.route_i_counts <> C2.route_i_counts AND A.route_i_counts <> C2.route_i_counts AND A.name <> B1.name AND B2.name <> C1.name AND C2.name <> D.name""")
            self.conn.commit()
            self.rows += self.cursor.fetchall()
            
        if _hops >= 4 :
        	self.cursor.execute(""f" SELECT distinct A.name, A.route_name, B2.name, B2.route_name, C2.name, C2.route_name, D2.name, D2.route_name, D.name FROM (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS A, (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS B1,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS B2,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS C1, (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS C2,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS D1,(SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.from_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS D2, (SELECT *FROM network_combined,stops,paris_routei_routename_routetype WHERE network_combined.to_stop_i = stops.stop_i AND paris_routei_routename_routetype.route_i = network_combined.route_i_counts) AS D WHERE A.name = $${_fromstation}$$ AND A.route_i_counts = B1.route_i_counts AND  B2.route_i_counts = C1.route_i_counts AND C2.route_i_counts = D1.route_i_counts AND D2.route_i_counts = D.route_i_counts AND  B1.name = B2.name  AND C1.name = C2.name AND D1.name = D2.name AND A.name <> B1.name AND B2.name <> C1.name AND C2.name <> D1.name AND D2.name <> D.name AND A.route_i_counts <> B2.route_i_counts AND B2.route_i_counts <> C2.route_i_counts AND C2.route_i_counts <> D2.route_i_counts AND A.route_i_counts <> D2.route_i_counts AND A.route_i_counts <> C2.route_i_counts AND D.name = $${_tostation}$$ """)
        	self.conn.commit()
        	self.rows += self.cursor.fetchall()
  	

        if len(self.rows) == 0 : 
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            return
            
        numrows = len(self.rows)
        numcols = len(self.rows[-1])
        #numcols = len(self.rows[-1]) - math.floor(len(self.rows[-1]) / 3.0) - 1 
        self.tableWidget.setRowCount(numrows)
        self.tableWidget.setColumnCount(numcols) 

        i = 0
        for row in self.rows : 
            j = 0
            #k = 0 
            for col in row :
                #if j % 3 == 0 : 
                
                    #k = k + 1
                #else : 
                    #self.tableWidget.setItem(i, j-k, QTableWidgetItem(str(col)))
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(col)))
                j = j + 1
            i = i + 1

        header = self.tableWidget.horizontalHeader()
        j = 0
        while j < numcols : 
            header.setSectionResizeMode(j, QHeaderView.ResizeToContents)
            j = j+1
        
        self.update()	
        


    def button_Clear(self):
        self.webView.clearMap(self.maptype_box.currentIndex())
        self.startingpoint = True
        self.update()


    def mouseClick(self, lat, lng):
        self.webView.addPointMarker(lat, lng)

        print(f"Clicked on: latitude {lat}, longitude {lng}")
        self.cursor.execute(""f" WITH mytable (distance, name) AS (SELECT ( ABS(latitude-{lat}) + ABS(longitude-{lng}) ), name FROM network_nodes,stops WHERE network_nodes.stop_i = stops.stop_i) SELECT A.name FROM mytable as A WHERE A.distance <=  (SELECT min(B.distance) FROM mytable as B)  """)
        self.conn.commit()
        rows = self.cursor.fetchall()
        #print('Closest STATION is: ', rows[0][0])
        if self.startingpoint :
            self.from_box.setCurrentIndex(self.from_box.findText(rows[0][0], Qt.MatchFixedString))
        else :
            self.to_box.setCurrentIndex(self.to_box.findText(rows[0][0], Qt.MatchFixedString))
        self.startingpoint = not self.startingpoint



class myWebView (QWebEngineView):
    def __init__(self):
        super().__init__()

        self.maptypes = ["OpenStreetMap", "Stamen Terrain", "stamentoner", "cartodbpositron"]
        self.setMap(0)


    def add_customjs(self, map_object):
        my_js = f"""{map_object.get_name()}.on("click",
                 function (e) {{
                    var data = `{{"coordinates": ${{JSON.stringify(e.latlng)}}}}`;
                    console.log(data)}}); """
        e = Element(my_js)
        html = map_object.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e

        return map_object


    def handleClick(self, msg):
        data = json.loads(msg)
        lat = data['coordinates']['lat']
        lng = data['coordinates']['lng']


        window.mouseClick(lat, lng)


    def addSegment(self, lat1, lng1, lat2, lng2):
        js = Template(
        """
        L.polyline(
            [ [{{latitude1}}, {{longitude1}}], [{{latitude2}}, {{longitude2}}] ], {
                "color": "red",
                "opacity": 1.0,
                "weight": 4,
                "line_cap": "butt"
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude1=lat1, longitude1=lng1, latitude2=lat2, longitude2=lng2 )

        self.page().runJavaScript(js)


    def addMarker(self, lat, lng):
        js = Template(
        """
        L.marker([{{latitude}}, {{longitude}}] ).addTo({{map}});
        L.circleMarker(
            [{{latitude}}, {{longitude}}], {
                "bubblingMouseEvents": true,
                "color": "#3388ff",
                "popup": "hello",
                "dashArray": null,
                "dashOffset": null,
                "fill": false,
                "fillColor": "#3388ff",
                "fillOpacity": 0.2,
                "fillRule": "evenodd",
                "lineCap": "round",
                "lineJoin": "round",
                "opacity": 1.0,
                "radius": 2,
                "stroke": true,
                "weight": 5
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude=lat, longitude=lng)
        self.page().runJavaScript(js)


    def addPointMarker(self, lat, lng):
        js = Template(
        """
        L.circleMarker(
            [{{latitude}}, {{longitude}}], {
                "bubblingMouseEvents": true,
                "color": 'green',
                "popup": "hello",
                "dashArray": null,
                "dashOffset": null,
                "fill": false,
                "fillColor": 'green',
                "fillOpacity": 0.2,
                "fillRule": "evenodd",
                "lineCap": "round",
                "lineJoin": "round",
                "opacity": 1.0,
                "radius": 2,
                "stroke": true,
                "weight": 5
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude=lat, longitude=lng)
        self.page().runJavaScript(js)


    def setMap (self, i):
        self.mymap = folium.Map(location=[48.8619, 2.3519], tiles=self.maptypes[i], zoom_start=12, prefer_canvas=True)

        self.mymap = self.add_customjs(self.mymap)

        page = WebEnginePage(self)
        self.setPage(page)

        data = io.BytesIO()
        self.mymap.save(data, close_file=False)

        self.setHtml(data.getvalue().decode())

    def clearMap(self, index):
        self.setMap(index)



class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        #print(msg)
        if 'coordinates' in msg:
            self.parent.handleClick(msg)


       
			
if __name__ == '__main__':
    app = QApplication(sys.argv) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
