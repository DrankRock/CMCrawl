import sys, re, csv
from graphics import QtWidgets, Ui_MainWindow
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QSpinBox, QComboBox, QFileDialog
from functionalCore import urlScrape

DEBUG = False


def errorDialog(error_message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Error")
    msg.setInformativeText(error_message)
    msg.setWindowTitle("Error")
    msg.exec_()


def debug_print(text):
    if DEBUG:
        print(text)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        self.run_url_btn.clicked.connect(self.runURL)
        self.cancel_url_btn.clicked.connect(self.generic_button_action)
        self.current_found_list = []
        self.init_table(self.current_list_table)
        self.init_table(self.found_items_table)
        self.bottom_list = []
        self.by_name.clicked.connect(self.sort_by_name)
        self.by_rarity.clicked.connect(self.sort_by_rarity)
        self.by_number.clicked.connect(self.sort_by_number)
        self.by_expansion.clicked.connect(self.sort_by_expansion)

        self.pushButton.clicked.connect(self.add_to_list)
        self.export_btn.clicked.connect(self.export)
        self.import_btn.clicked.connect(self.import_file)

        self.increasing.setChecked(True)

    def init_table(self, table):
        table.setColumnCount(7)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)

    def sort_by_name(self):
        self.sort_found_list(type=2)

    def sort_by_rarity(self):
        self.sort_found_list(type=3)

    def sort_by_number(self):
        self.sort_found_list(type=1)

    def sort_by_expansion(self):
        self.sort_found_list(type=0)

    def generic_button_action(self):
        debug_print("Oh hi there ! - {}".format(self.increasing.isChecked()))

    def runURL(self):
        self.found_items_table.clear()
        pattern = re.compile("^https:\/\/www\.cardmarket\.com\/.*")
        url = self.url_input_line_edit.text()
        if not pattern.match(url):
            errorDialog("Error : url is incorrect")
            return
        else:
            self.current_found_list = urlScrape(url)
            self.fill_table(self.current_found_list, self.found_items_table)

    def condition_combo_box(self):
        combo = QComboBox()
        combo.addItems(["none", "MT", "NM", "EX", "GD", "LP", "PL", "PO"])
        return combo

    # fill the top table containing the result of the scraping
    def fill_table(self, filler_list, table):
        debug_print("-- fill table : {}".format(table.objectName()))
        number_of_results = len(filler_list)
        table.setRowCount(number_of_results)
        for row, line in enumerate(filler_list):
            debug_print(row)
            for col, elem in enumerate(line):
                debug_print(elem)
                if col == 4:
                    spinbox = QSpinBox()
                    spinbox.setValue(int(elem))
                    table.setCellWidget(row, col, spinbox)
                if col == 5:
                    combobox = self.condition_combo_box()
                    if elem != 0:
                        combobox.setCurrentText(elem)
                    table.setCellWidget(row, col, combobox)
                else:
                    table.setItem(row, col, QTableWidgetItem(elem))

    # sort the top table
    # This deletes the values of the spinBox / combobox. Avoiding this is possible but troublesome
    def sort_found_list(self, type=1):
        # type 0 = Expansion, 1 = Number, 2 = Name, 3 = Rarity

        # There is a way to keep values, with a dict, conteianing "exp|num|name" : <int>
        # And updating this dict before sorting, then updating the table after filling
        # same should be done for the combobox

        self.current_found_list = sorted(self.current_found_list, key=lambda x: x[type],
                                         reverse=(not self.increasing.isChecked()))
        self.fill_table(self.current_found_list, self.found_items_table)

    def add_to_list(self):
        self.bottom_list = self.table_to_list(self.found_items_table)
        self.fill_table(self.bottom_list, self.current_list_table)

    def table_to_list(self, table):
        output = []
        for i in range(0, table.rowCount()):
            number_of_item = table.cellWidget(i, 4).value()
            if number_of_item > 0:
                output.append([
                    self.found_items_table.item(i, 0).text(),
                    self.found_items_table.item(i, 1).text(),
                    self.found_items_table.item(i, 2).text(),
                    self.found_items_table.item(i, 3).text(),
                    number_of_item,
                    self.found_items_table.cellWidget(i, 5).currentText(),
                    self.found_items_table.item(i, 6).text()
                ])
        return output

    def export(self):
        file_name = self.file_dialog()
        fields = ['Expansion', 'Number', 'Name', 'Rarity', 'Quantity', 'Condition', 'URL']
        new_list = self.table_to_list(self.current_list_table)
        with open(file_name, 'w') as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(new_list)

    def import_file(self):
        file_name = self.file_dialog(1)
        with open(file_name, 'r') as f:
            data = list(csv.reader(f, delimiter=","))
            if data[0][0] == "Expansion" and data[0][1] == "Number":
                data = data[1:]
            self.current_found_list += data[1:]
            self.fill_table(self.bottom_list, self.current_list_table)

    def file_dialog(self, type=0):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if type == 0:
            filename, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                      "All Files (*);;Python Files (*.py)", options=options)
        else:
            filename, _ = QFileDialog.getOpenFileName(self, "QFileDialog.geOpenFileName()", "",
                                                      "All Files (*);;Python Files (*.py)", options=options)
        if filename:
            return filename


def graphic():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


graphic()
