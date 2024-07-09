from get_data import LabelData
from label_print import LabelPrint

if __name__ == "__main__":
  exp = LabelData('./ordem.xlsx')
  exp.print_data()
  lb = LabelPrint(exp.get_data('OP-0216534'))
  lb.create_label()