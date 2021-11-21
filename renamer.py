import os, sys, time, re, json
from send2trash import send2trash
from PIL import Image
from PyQt5.QtWidgets import QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStyle, QVBoxLayout, QWidget, QSplitter, QFrame, QSizePolicy, QScrollArea, QMenu, QMessageBox, QDialog, QRadioButton
from PyQt5.QtGui import QPixmap, QPalette, QIcon, QTransform
from PyQt5.QtCore import QDir, pyqtSignal, QSize, QTimer, QEvent, QObject
from PyQt5.QtCore import Qt

stylesheet = """
	QWidget {
    background: rgb(23, 23, 23);
    border: none;
    font: bold large;
    color: rgb(153, 153, 153);
	}
	QFrame {
    background: rgb(123, 123, 123);
    border: 10px ; border-color: white;
    font: bold large;
    color: rgb(153, 153, 153);
	}
	QPushButton {
	    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
	    stop:0 rgb(84, 84, 84), stop:1 rgb(53, 53, 53));
	}
	QPushButton:hover {
	    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
	    stop:0 rgb(79, 99, 44), stop:1 rgb(59, 75, 29));
	    color: rgb(194, 224, 104);
	}
	QPushButton:disabled {
		background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    	stop:0 rgb(113, 113, 113), stop:1 rgb(103, 103, 103));
    	color: rgb(133, 133, 133);
	}
	QLineEdit {
    border-width: 1px;
    border-style: solid;
    border-color: rgb(153, 153, 153);
    background: rgb(53, 53, 53);
	}
	QSplitter::handle:vertical {
	    height: 10px;
	}
"""

class FolderBrowser(QWidget):
	folderChanged = pyqtSignal(str)
	refreshPrompt = pyqtSignal()

	@property
	def folder(self):
		return self._folder

	@folder.setter
	def folder(self, value):
		self._folder = value

	def __init__(self, folder):
		super(FolderBrowser, self).__init__()
		self.folder = folder

		self.setLayout(QHBoxLayout())

		icon = self.style().standardIcon(QStyle.SP_DialogOpenButton)
		self.folderBrowserBtn = QPushButton(icon, "")
		self.folderBrowserBtn.setFixedSize(24, 24)
		self.folderBrowserBtn.clicked.connect(self.browse_)
		self.layout().addWidget(self.folderBrowserBtn)

		self.folderEdit = QLineEdit("")
		self.layout().addWidget(self.folderEdit)

		icon = self.style().standardIcon(QStyle.SP_BrowserReload)
		self.folderRefreshBtn = QPushButton(icon, "")
		self.folderRefreshBtn.setFixedSize(24, 24)
		self.folderRefreshBtn.clicked.connect(self.refresh)
		self.layout().addWidget(self.folderRefreshBtn)

	def browse_(self):
		folder = str(QFileDialog.getExistingDirectory(parent = self, directory=self.folder, caption="Select Directory"))
		if folder:
			folder = QDir.toNativeSeparators(folder)
			if self.folder != folder:
				self.folder = folder
				self.folderChanged.emit(self.folder)

	def refresh(self):
		self.refreshPrompt.emit()


class ImageDisplay(QWidget):
	@property
	def currentFile(self):
		try:
			return os.path.join(os.sep, self.folder, self.images[self.id])
		except:
			return None

	@property
	def currentImage(self):
		try:
			return self.images[self.id]
		except:
			return None

	@property 
	def folder(self):
		return self._folder

	@folder.setter
	def folder(self, folder):
		self._folder = folder
		self.init_folder()

	@property 
	def id(self):
		return self._id

	@id.setter
	def id(self, value):
		if value>=0 and value<len(self.images):
			self._id = value
			self.load_img()
			self.display()

	@property 
	def imgSize(self):
		size = QSize(0, 0)
		sw = self.width()-20
		sh = self.height()-40
		if sh:
			sr = sw/sh

			w = self.pixmap.width()
			h = self.pixmap.height()
			r = w/h

			#if the ratio of the image is more horizontal than the layout
			if r >= sr:
				size = QSize(int(sh * sr), int(sh))
			else:
				size = QSize(int(sw), int(sw / sr))

		return size

	def __init__(self, folder):
		super(ImageDisplay, self).__init__()
		self.acceptable_formats = ["JPG", "JPEG", "PNG", "GIF", "WEBP", "TIFF", "PSD",
						"RAW", "BMP", "HEIF", "INDD", "JPEG 2000", "SVG", 
						"AI", "EPS", "PDF", "EXR", "TGA"]
		self.images = []
		self._id = 0

		self.setLayout(QHBoxLayout())

		self.leftBtn = QPushButton("<")
		self.leftBtn.setMinimumWidth(80)
		self.leftBtn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
		self.leftBtn.clicked.connect(self.previousPhoto)
		self.leftBtn.setEnabled(False)
		self.leftBtn.setStyleSheet(" font-size: 40px; ")
		self.layout().addWidget(self.leftBtn)
		self.layout().addStretch()

		self.imgLayout = QVBoxLayout()
		self.layout().addLayout(self.imgLayout)

		self.imgLayout.addStretch()
		self.img = QLabel("")
		self.img.setAlignment(Qt.AlignCenter)
		self.imgLayout.addWidget(self.img)

		self.label = QLabel("")
		self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.label.setMinimumSize(1, 1)
		self.label.setAlignment(Qt.AlignCenter)
		self.imgLayout.addWidget(self.label)
		self.imgLayout.addStretch()

		self.layout().addStretch()

		self.rightBtn = QPushButton(">")
		self.rightBtn.setMinimumWidth(80)
		self.rightBtn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
		self.rightBtn.clicked.connect(self.nextPhoto)
		self.rightBtn.setEnabled(False)
		self.rightBtn.setStyleSheet(" font-size: 40px; ")
		self.layout().addWidget(self.rightBtn)
		self.folder = folder


	def init_folder(self):
		self.init_images()
		if self.images:
			self.id = 0

	def display(self):
		if self.images:
			qsize = self.imgSize
			self.img.resize(qsize)

			#this is necessary to allow the widget to shrink down properly
			self.img.setMinimumSize(1, 1)

			self.img.setPixmap(self.pixmap.scaled(qsize, Qt.KeepAspectRatio))
			self.label.setText(self.images[self.id])
			self.handle_buttons()

	def init_images(self):
		files = os.listdir(self.folder)
		images = []
		for file in files:
			name, ext = os.path.splitext(file)
			if ext.upper()[1::] in self.acceptable_formats:
				images.append(file)
		if images:
			self.images = images
	
	def init_id(self):
		self.id = 0

	def load_img(self):
		img = self.currentFile
		if img:
			self.pixmap = QPixmap(img)

	def handle_buttons(self):
		if not len(self.images):
			self.rightBtn.setEnabled(False)
			self.leftBtn.setEnabled(False)
		else:
			if len(self.images)-1 > self.id:
				self.rightBtn.setEnabled(True)
			else:
				self.rightBtn.setEnabled(False)

			if self.id > 0:
				self.leftBtn.setEnabled(True)
			else:
				self.leftBtn.setEnabled(False)

	def previousPhoto(self):
		if self.images:
			self.id -= 1

	def nextPhoto(self):
		if self.images:
			self.id += 1

	def accept(self, newname):
		self.images[self.id] = newname
		self.nextPhoto()

	def refreshFile(self):
		self.load_img()
		self.display()

	def refresh(self):
		files = os.listdir(self.folder)
		new_list = []
		#removing old images
		for i, image in enumerate(self.images):
			if image in files:
				new_list.append(image)
				if i == self.id:
					self.id_ = len(new_list)-1

		#adding new images
		for file in files:
			if not file in new_list:
				name, ext = os.path.splitext(file)
				if ext.upper()[1::] in self.acceptable_formats:
					new_list.append(file)

		self.images = new_list
		self.display()

	def resizeImages(self):
		self.display()

	def resizeEvent(self, e):
		self.resizeImages()
		super(ImageDisplay, self).resizeEvent(e)

	def discardCurrent(self):
		del self.images[self.id]
		if self.id < len(self.images):
			self.id = self.id
		else:
			self.id = self.id-1

class RenamableLabel(QWidget):
	def __init__(self, text):
		super(RenamableLabel, self).__init__()

		self.setLayout(QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.label = QLabel(text)
		self.layout().addWidget(self.label)
		self.edit = QLineEdit("")
		self.edit.editingFinished.connect(self.completeEdit)
		self.edit.hide()
		self.layout().addWidget(self.edit)

		self.timer = QTimer()
		self.timer.setInterval(250)
		self.timer.setSingleShot(True)
		self.timer.timeout.connect(self.timeout)
		self.click_count = 0

	def timeout(self):
		if self.click_count == 1:
			self.singleClick()
		elif self.click_count > 1:
			self.doubleClick()
		self.click_count = 0

	def mousePressEvent(self, e):
		self.click_count += 1
		if not self.timer.isActive():
			self.timer.start()

	def singleClick(self):
		pass

	def doubleClick(self):
		self.edit.setText(self.text())
		self.label.hide()
		self.edit.show()
		self.edit.selectAll()
		self.edit.setFocus(True)

	def text(self):
		return self.label.text()

	def setText(self, text):
		self.label.setText(text)

	def setAlignment(self, alignment):
		self.label.setAlignment(alignment)
		self.edit.setAlignment(alignment)

	def isEditted(self):
		return not self.edit.isHidden()

	def completeEdit(self):
		self.setText(self.edit.text())
		self.edit.hide()
		self.label.show()

class Tag(QWidget):
	deleteSg = pyqtSignal()
	def __init__(self, name, checked=False):
		super(Tag, self).__init__()
		self.name = name

		self.setLayout(QHBoxLayout())
		self.layout().setSpacing(0)
		self.layout().setContentsMargins(0, 0, 0, 0)

		self.chk = QCheckBox(self.name)
		if checked:
			self.chk.setCheckState(Qt.Checked)
		self.layout().addWidget(self.chk)

		self.removeBtn = QPushButton("X")
		self.removeBtn.clicked.connect(self.delete)
		self.removeBtn.setFixedSize(20, 20)
		self.layout().addWidget(self.removeBtn)

	def delete(self):
		self.deleteSg.emit()

	def isChecked(self):
		return self.chk.isChecked()

class TagsTemplate(QWidget):
	tabDeletedSg = pyqtSignal()
	@property
	def name(self):
		return self.title.text()

	@property
	def availableNames(self):
		return [x.name for x in self.widgets]

	@property
	def checkedNames(self):
		return [x.name for x in self.widgets if x.isChecked()]
	
	def __init__(self, name, names):
		super(TagsTemplate, self).__init__()

		stylesheet = """
			QWidget {
		    background: rgb(63, 63, 63);
		    border: none;
		    font: bold large;
		    color: rgb(153, 153, 153);
			}
			QFrame {
		    background: rgb(63, 63, 63);
		    border: 10px ; border-color: white;
		    font: bold large;
		    color: rgb(153, 153, 153);
			}
			QPushButton {
			    background: none;
			}
			QPushButton:hover {
			    background-color: rgb(79, 99, 44);
			    color: rgb(194, 224, 104);
			}
			QPushButton:disabled {
				background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
		    	stop:0 rgb(113, 113, 113), stop:1 rgb(103, 103, 103));
		    	color: rgb(133, 133, 133);
			}
			QLineEdit {
		    border-width: 1px;
		    border-style: solid;
		    border-color: rgb(153, 153, 153);
		    background: rgb(53, 53, 53);
		    padding: 1px 0px 2px 0px;
			}
			QSplitter::handle:vertical {
			    height: 10px;
			}
			QLabel {
				border-radius: 2px;
				padding: 3px 0px 5px 0px;
			}
			QCheckBox:hover {
			    background-color: rgb(79, 99, 44);
			    color: rgb(194, 224, 104);
			}
		"""
		self.setStyleSheet(stylesheet)

		self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
		self.names = names
		self.widgets = []
		self.setLayout(QVBoxLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().setSpacing(0)

		self.title = RenamableLabel(name)
		self.title.setAlignment(Qt.AlignCenter)
		self.layout().addWidget(self.title)

		self.scroll = QScrollArea()
		self.layout().addWidget(self.scroll)

		#this is necessary for the widget to take an appropriate size
		self.scroll.setWidgetResizable(False)
		self.scroll.setWidgetResizable(True)

		self.widget = QWidget()
		self.scroll.setWidget(self.widget)

		self.widget.setLayout(QVBoxLayout())

	def deleteWidget(self, w):
		self.widgets.remove(w)
		w.deleteLater()

	def addName(self):
		txt = self.extraEdit.text()
		if txt and not txt in self.availableNames:
			w = Tag(txt)
			self.widget.layout().insertWidget(len(self.widgets), w)
			self.widgets.append(w)
			w.deleteSg.connect(lambda x=w:self.deleteWidget(x))
			self.extraEdit.clear()

	def tags(self, file):
		return self.checkedNames()

	def checkedNames(self):
		return [x.name for x in self.widgets if x.isChecked()]

	def state(self):
		output = []
		for w in self.widgets:
			output.append(
			{"name":w.name,
			"checked":w.isChecked()})
		return output

	def addWidget(self, w):
		self.widget.layout().addWidget(w)

	def addStretch(self):
		self.widget.layout().addStretch()

	def contextMenuEvent(self, event):
		contextMenu = QMenu(self)
		deleteAct = contextMenu.addAction("Delete Tab")
		action = contextMenu.exec_(self.mapToGlobal(event.pos()))
		if action == deleteAct:
			ret = QMessageBox.question(self,'', "Do you really want to delete the tab?", QMessageBox.Yes | QMessageBox.No)
			if ret == QMessageBox.Yes:
				self.tabDeletedSg.emit()
		
class TagsTab(TagsTemplate):
	@property
	def tabType(self):
		return "TagsTab"

	def __init__(self, name, names):
		super(TagsTab, self).__init__(name, names)

		# stylesheet = """
		# 	QWidget {
		#     background: rgb(63, 63, 63);
		#     border: none;
		#     font: bold large;
		#     color: rgb(153, 153, 153);
		# 	}
		# 	QFrame {
		#     background: rgb(63, 63, 63);
		#     border: 10px ; border-color: white;
		#     font: bold large;
		#     color: rgb(153, 153, 153);
		# 	}
		# 	QPushButton {
		# 	    background: none;
		# 	}
		# 	QPushButton:hover {
		# 	    background-color: rgb(79, 99, 44);
		# 	    color: rgb(194, 224, 104);
		# 	}
		# 	QPushButton:disabled {
		# 		background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
		#     	stop:0 rgb(113, 113, 113), stop:1 rgb(103, 103, 103));
		#     	color: rgb(133, 133, 133);
		# 	}
		# 	QLineEdit {
		#     border-width: 1px;
		#     border-style: solid;
		#     border-color: rgb(153, 153, 153);
		#     background: rgb(53, 53, 53);
		#     padding: 1px 0px 2px 0px;
		# 	}
		# 	QSplitter::handle:vertical {
		# 	    height: 10px;
		# 	}
		# 	QLabel {
		# 		border-radius: 2px;
		# 		padding: 3px 0px 5px 0px;
		# 	}
		# 	QCheckBox:hover {
		# 	    background-color: rgb(79, 99, 44);
		# 	    color: rgb(194, 224, 104);
		# 	}
		# """
		# self.setStyleSheet(stylesheet)

		for i in names:
			w = Tag(i["name"], i["checked"])
			self.addWidget(w)
			self.widgets.append(w)

			w.deleteSg.connect(lambda x=w:self.deleteWidget(x))

		self.extraEdit = QLineEdit()
		self.extraEdit.returnPressed.connect(self.addName)
		self.addWidget(self.extraEdit)

		self.addStretch()

class DateTab(TagsTemplate):
	@property
	def tabType(self):
		return "DateTab"
	
	def __init__(self, content=""):
		super(DateTab, self).__init__("date", [])

		self.dateEdit = QLineEdit("YYYY_MM")
		if content:
			self.dateEdit.setText(content)

		self.addWidget(self.dateEdit)

		self.addStretch()

	def tags(self, file):
		txt = self.dateEdit.text()
		if txt:
			date = os.path.getmtime(file)
			gmtime = time.gmtime(date)

			year = time.strftime("%Y", gmtime)
			month = time.strftime("%m", gmtime)
			day = time.strftime("%d", gmtime)

			tmpstr = txt[::-1]

			reay = year[::-1]
			while(re.search("Y", tmpstr)):
				if not len(reay):
					reay = "0"
				tmpstr = re.sub(r"Y", reay[0], tmpstr, 1, re.MULTILINE)
				reay = reay[1::]

			htnom = month[::-1]
			while(re.search("M", tmpstr)):
				if not len(htnom):
					htnom = "0"
				tmpstr = re.sub(r"M", htnom[0], tmpstr, 1, re.MULTILINE)
				htnom = htnom[1::]

			yad = day[::-1]
			while(re.search("D", tmpstr)):
				if not len(yad):
					yad = "0"
				tmpstr = re.sub(r"D", yad[0], tmpstr, 1, re.MULTILINE)
				yad = yad[1::]

			return [tmpstr[::-1]]
		return []

	def state(self):
		return self.dateEdit.text()

class NewTabDialog(QDialog):
	@property
	def tab(self):
		if self.regularTabRdb.isChecked():
			return "regular"
		elif self.dateTabRdb.isChecked():
			return "date"
	
	def __init__(self):
		super(NewTabDialog, self).__init__()
		self.setLayout(QVBoxLayout())
		self.regularTabRdb = QRadioButton("regular tab")
		self.regularTabRdb.setChecked(Qt.Checked)
		self.dateTabRdb = QRadioButton("date tab")
		self.layout().addWidget(self.regularTabRdb)
		self.layout().addWidget(self.dateTabRdb)

		self.btnLayout = QHBoxLayout()
		self.layout().addLayout(self.btnLayout)

		self.okBtn = QPushButton("OK")
		self.okBtn.clicked.connect(self.accept)
		self.btnLayout.addWidget(self.okBtn)

		self.cancelBtn = QPushButton("Cancel")
		self.cancelBtn.clicked.connect(self.reject)
		self.btnLayout.addWidget(self.cancelBtn)

class TagsManager(QWidget):
	@property
	def state(self):
		output = []
		for w in self.tagstabs:
			tab = {"name":w.name, "content":[], "type":w.tabType}
			tab["content"] = w.state()
			output.append(tab)
		return output
	
	def __init__(self, state):
		super(TagsManager, self).__init__()
		self.setLayout(QHBoxLayout())
		self.layout().setAlignment(Qt.AlignTop)
		self.tagstabs = []

		if state:
			try:
				widgets = []
				for tab in state:
					if tab["type"] == "DateTab":
						w = DateTab(tab["content"])
						w.tabDeletedSg.connect(lambda x=w:self.tabDelete(x))
						widgets.append(w)
					elif tab["type"] == "TagsTab":
						w = TagsTab(tab["name"], tab["content"])
						w.tabDeletedSg.connect(lambda x=w:self.tabDelete(x))
						widgets.append(w)

				for w in widgets:
					self.tagstabs.append(w)
					self.layout().addWidget(w)
			
			except Exception as e:
				print(e)
				print("failed to load config. Skipping.")

		else:
			for i, nm in enumerate(["date", "place", "name"]):
				if i == 0:
					names = []
					w = DateTab()
				if i == 1:
					tags = [{"name":"Dunkerque", "checked":False}, 
							{"name":"Paris", "checked":False},
							{"name":"Montreal", "checked":False}]
					w = TagsTab(nm, tags)
				if i == 2:
					tags = [{"name":"Justine", "checked":False}, 
							{"name":"Victor", "checked":False},
							{"name":"Curu", "checked":False}]
					w = TagsTab(nm, tags)

				self.tagstabs.append(w)
				self.layout().addWidget(w)

		self.addBtn = QPushButton("+")
		self.addBtn.clicked.connect(self.newTabRequest)
		self.addBtn.setFixedWidth(35)
		self.addBtn.setMaximumHeight(190)
		self.addBtn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
		self.addBtn.setStyleSheet(" font-size: 25px; ")
		self.layout().addWidget(self.addBtn)
		self.layout().addStretch()

	def tags(self, file):
		tags = []
		for w in self.tagstabs:
			for t in w.tags(file):
				tags.append(t)
		return tags

	def tabDelete(self, w):
		self.tagstabs.remove(w)
		w.deleteLater()

	def newTabRequest(self):
		dialog = NewTabDialog()
		ret = dialog.exec()
		if ret:
			if dialog.tab == "regular":
				w = TagsTab("misc", [])
				w.tabDeletedSg.connect(lambda x=w:self.tabDelete(x))
				self.tagstabs.append(w)
				self.layout().insertWidget(len(self.tagstabs)-1, w)
			elif dialog.tab == "date":
				w = DateTab("YYYY_MM")
				w.tabDeletedSg.connect(lambda x=w:self.tabDelete(x))
				self.tagstabs.append(w)
				self.layout().insertWidget(len(self.tagstabs)-1, w)

	def acceptTabsNames(self):
		for tab in self.tagstabs:
			if tab.title.isEditted():
				tab.title.completeEdit()

class MainWindow(QWidget):
	def __init__(self, folder):
		super(MainWindow, self).__init__()
		self.setWindowTitle("Photos renamer")
		self.resize(1200, 800)
		self.folder = folder
		
		self.setLayout(QVBoxLayout())

		self.splitter = QSplitter(Qt.Vertical)

		self.topWidget = QFrame()
		self.topWidget.setFrameShape(QFrame.StyledPanel)
		self.topWidget.setLayout(QVBoxLayout())
		self.topWidget.layout().setSpacing(0)
		self.topWidget.layout().setContentsMargins(0, 0, 0, 0)

		self.bottomWidget = QFrame()
		self.bottomWidget.setFrameShape(QFrame.StyledPanel)
		self.bottomWidget.setLayout(QVBoxLayout())
		self.bottomWidget.layout().setSpacing(0)
		self.bottomWidget.layout().setContentsMargins(0, 0, 0, 0)

		self.folderBrowser = FolderBrowser(self.folder)
		self.folderBrowser.folderChanged.connect(self.folderChange)
		self.folderBrowser.refreshPrompt.connect(self.refreshPrompt)
		self.topWidget.layout().addWidget(self.folderBrowser)

		self.imageDisplay = ImageDisplay(self.folder)
		self.topWidget.layout().addWidget(self.imageDisplay)

		self.btnLayout = QHBoxLayout()
		self.bottomWidget.layout().setSpacing(2)
		self.bottomWidget.layout().setContentsMargins(2, 2, 2, 2)

		self.deleteImgBtn = QPushButton("")
		self.deleteImgBtn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
		self.deleteImgBtn.setFixedSize(35,35)
		self.deleteImgBtn.clicked.connect(self.deleteImg)
		self.btnLayout.addWidget(self.deleteImgBtn)

		self.rotateImgClBtn = QPushButton("")
		self.rotateImgClBtn.setFixedSize(35,35)
		# self.rotateIconPixmap = QPixmap("./icons/rotate_clockwise.png")
		self.rotateIconPixmap = QPixmap(resource_path("rotate_clockwise.png"))
		self.rotateClIcon = QIcon(self.rotateIconPixmap)
		self.rotateImgClBtn.setIcon(self.rotateClIcon)
		self.rotateImgClBtn.clicked.connect(lambda:self.rotateImg(1))
		self.btnLayout.addWidget(self.rotateImgClBtn)

		self.rotateImgCClBtn = QPushButton("")
		self.rotateImgCClBtn.setFixedSize(35,35)
		transform = QTransform().scale(-1.0, 1.0)
		self.rotateCClIcon = QIcon(self.rotateIconPixmap.transformed(transform, Qt.SmoothTransformation))
		self.rotateImgCClBtn.setIcon(self.rotateCClIcon)
		self.rotateImgCClBtn.clicked.connect(lambda:self.rotateImg(-1))
		self.btnLayout.addWidget(self.rotateImgCClBtn)

		self.btnLayout.addStretch(2)

		self.renameBtn = QPushButton("Rename")
		self.renameBtn.setFixedWidth(200)
		self.renameBtn.setMinimumHeight(35)
		self.renameBtn.clicked.connect(self.rename)
		self.btnLayout.addWidget(self.renameBtn)

		self.btnLayout.addStretch(3)

		self.bottomWidget.layout().addLayout(self.btnLayout)

		self.tagsManager = TagsManager(self.loadState())
		self.bottomWidget.layout().addWidget(self.tagsManager)

		self.splitter.addWidget(self.topWidget)
		self.splitter.addWidget(self.bottomWidget)
		self.splitter.setSizes([800, 100])
 		
		self.layout().addWidget(self.splitter)

		self.setStyleSheet(stylesheet)

	def folderChange(self, folder):
		self.folder = folder
		self.imageDisplay.folder = self.folder

	def refreshPrompt(self):
		self.imageDisplay.refresh()

	def deleteImg(self):
		currentFile = self.currentFile()
		if currentFile:
			ret = QMessageBox.question(self,'', "Do you really want to delete the file?", QMessageBox.Yes | QMessageBox.No)
			if ret == QMessageBox.Yes:
				try:
					send2trash(currentFile)
					self.imageDisplay.discardCurrent()
				except Exception as e:
					print(e)
					print("failure to delete the file %s" % currentFile)

	def rotateImg(self, direction):
		currentFile = self.currentFile()
		if currentFile:
			try:
				im = Image.open(currentFile)
				if direction == 1:
					im = im.transpose(Image.ROTATE_270)
				elif direction == -1:
					im = im.transpose(Image.ROTATE_90)
				im.save(currentFile)
				self.imageDisplay.refreshFile()
			except Exception as e:
				print(e)

	def rename(self):
		currentFile = self.currentFile()
		if currentFile:
			tags = self.tagsManager.tags(currentFile)
			if tags:
				fullname, ext = os.path.splitext(currentFile)
				path, name = os.path.split(fullname)
				newname = "_".join(tags)
				newfilename = os.path.join(os.sep, path, newname+ext)
				if newfilename == currentFile:
					print("Same name requested. Skipping.")
					return
				fileId = 1
				while(os.path.isfile(newfilename)):
					fileId += 1
					newname = "_".join(tags)+"_"+str(fileId)
					newfilename = os.path.join(os.sep, path, newname+ext)

				try:
					print("renaming %s to %s" %(name+ext, newname+ext))
					os.rename(currentFile, newfilename)
					self.accept(newname+ext)
				except Exception as e:
					print(e)

	def accept(self, newname):
		self.imageDisplay.accept(newname)

	def currentFile(self):
		return self.imageDisplay.currentFile

	def saveState(self):
		home = os.path.expanduser("~")
		configFile = os.path.join(home, ".photorenamerconfig")

		# config = {}
		# config["tab"] = self.tagsManager.state
		config = self.tagsManager.state
		try:
			with open(configFile, 'w') as f:
				json.dump(config, f, indent=4)
		except Exception as e:
			print(e)
			print("failed to save config")

	def loadState(self):
		home = os.path.expanduser("~")
		configFile = os.path.join(home, ".photorenamerconfig")
		if os.path.isfile(configFile):
			with open(configFile, 'r') as f:
				config = json.load(f)
				return config

	def mousePressEvent(self, e):
		self.tagsManager.acceptTabsNames()
		super(MainWindow, self).mousePressEvent(e)

	def closeEvent(self, e):
		self.saveState()
		super(MainWindow, self).closeEvent(e)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Logo = resource_path("Logo.png")
app = QApplication(sys.argv)
window = MainWindow("C:")
# window = MainWindow("D:\\__Personnel\\Photos\\1ere annee au canada 2015 hiver printemps\\")
window.show()
app.exec()
