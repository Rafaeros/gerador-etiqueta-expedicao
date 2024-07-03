from get_data import LabelData
from label_print import LabelPrint

exp = LabelData('./ordem.xlsx')
exp.print_data()
exp.get_data('OP-0216534')

lb = LabelPrint(exp.get_data('OP-0215869'))
lb.create_label()

if __name__ == "__main__":
  print("Hello World")