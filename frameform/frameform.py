# -*- coding: utf-8 -*-
"""
Created on Tue May 30 08:54:29 2017

@author: jmccrary
"""

import pandas as pd
import numpy as np
from IPython.display import display
from ipywidgets import (Button, Checkbox, HBox, VBox, Layout, 
                        IntText, FloatText, Text, ToggleButton)

CASTERS = {Checkbox: lambda x: bool(x),
           IntText: lambda x: int(x),
           FloatText: lambda x: float(x),
           Text: lambda x: str(x)}

__version__ = '0.8.0'


class TableHandler(object):
    """A class to bound methods with pointers to data in a DataFrame onto widgets
    since the widget.observe() method only accepts one argument 'change'
    """
    def __init__(self, table):
        self.table = table
        
    def apply_value(self, change):
        # change is a dict with pointer to 'owner' widget
        me = change['owner']
        # print("My location is row %d and col %d" %(me.j, me.i))
        # use the 'tableCell's indices to inject it's value into the data matrix
        self.table.data.iloc[me.i, me.j] = me.value
       
    
def _type_to_widget(dtype_name):
    """From 
    
    dtype_name : str, name of the data type
    
    returns an appropriate widget to represent the data
    """
    if dtype_name == 'bool':
        return Checkbox
    elif 'int' in dtype_name:
        return IntText
    elif 'float' in dtype_name:
        return FloatText
    else:
        return Text


def _content_to_layout(series):
    if isinstance(series, pd.Index):
        if 'int' in series.dtype.name:
            tot_width = np.ceil(np.log10(series.max()))*8 + 16
        else:
            lengths = [len(i) for i in series]
            tot_width = np.max(lengths)*8 + 16
            
    elif series.dtypes.name == 'bool':
        tot_width = (len(str(series.name)) + 4)*8 + 16
        check_margin = (tot_width - 12) // 2
        title_layout = Layout(width='{}px'.format(tot_width - 1), padding='0px 8px 0px 8px')
        content_layout = Layout(width='12px',
                                margin='3px {}px 0px {}px'.format(check_margin,
                                                                  check_margin))
        return [title_layout, content_layout]
    
    elif 'int' in series.dtypes.name:
        max_val_len = int(np.ceil(np.log10(series.max())))
        s_name_len = len(str(series.name)) + 4
        tot_width = np.max([max_val_len, s_name_len])*8 + 16
        
    elif 'float' in series.dtypes.name:
        max_val_len = 15 + 2  # ie the number of significant digits for a 'float64' plus a decimal and leading 0
        s_name_len = len(str(series.name)) + 4
        tot_width = np.max([max_val_len, s_name_len])*8 + 16
        
    else:
        tot_width = 24*8 + 16

    title_layout = Layout(width='{}px'.format(tot_width - 1), padding='0px 8px 0px 8px')
    content_layout = Layout(width='{}px'.format(tot_width))
    return [title_layout, content_layout]

        
class FrameEditor(object):
    """Create and edit forms with pandas.DataFrames in Jupyter Notebooks

    """
    def __init__(self, df, inplace=False, auto_display=True):
        """Build a form from a DataFrame that edits the values in the frame

        :param df a pandas.DataFrame instance that isn't too large
                (less than 12 columns and less than 40 rows)
        :param inplace, bool default False, when True initializer DataFrame's
                values will be updated with the values input into the form
        :param auto_display default True, display the form when returning the
                FrameEditor instance's representation

        examples:
        form = FrameEditor(df, inplace=True, auto_display=False)
        form.display()

        form = FrameEditor(df)
        form
        """
        cls = len(df.columns)
        rws = len(df.index)
        dtype = [dt.name for dt in df.dtypes]
        layout = [_content_to_layout(df[col_name]) for col_name in df.columns]

        self._auto_display = auto_display
        self._df = df if inplace else df.copy()
        self.row_names = df.index.astype(str)
        self.col_names = df.columns.astype(str)
        
        index_layout = _content_to_layout(df.index)
        # set a blank Label in the first column of the header
       
        self._widget_rows = [HBox([Button(description=' ', disabled=True, layout=index_layout[0])]
                                  + [Button(disabled=True, layout=layout[j][0],
                                            description=c_n) for j, c_n in enumerate(self.col_names)])]
        
        # both of the following are a list of lists, need to initialize outer
        # prior to loops
        self.cells = []
        self.banner = []
        
        for i in range(rws):
            self.cells.append([])  # append an empty list for new row
            for j in range(cls):
                cell_widget = _type_to_widget(dtype[j])
                caster = CASTERS[cell_widget]
                if dtype[j] == 'bool':
                    self.cells[i].append(cell_widget(value=bool(self._df.iloc[i, j]),
                                                     layout=layout[j][1],
                                                     tooltip='{}, {}'.format(self.col_names[j],
                                                                             self.row_names[i])))
                    self.cells[i][-1].indent = False
                else:
                    self.cells[i].append(cell_widget(value=caster(self._df.iloc[i, j]),
                                                     layout=layout[j][1],
                                                     tooltip='{}, {}'.format(self.col_names[j],
                                                                             self.row_names[i])))
                self.cells[i][-1].i = i
                self.cells[i][-1].j = j
                self.cells[i][-1].observe(TableHandler(self).apply_value, 'value')

            self._widget_rows.append(HBox([Button(disabled=True, layout=index_layout[1],
                                                  description=self.row_names[i])] + self.cells[i]))
        table_layout = Layout(flex_flow='column wrap')
        self._table = HBox(self._widget_rows, layout=table_layout)

    @property
    def data(self):
        return self._df

    @data.setter
    def data(self, value):
        """Needs to do some check on 'value' and the actual data and shape or
        just warn that the 'setter' does nothing and that table.data
        population is required through the 'Cell' objects

        _data = self.data

        self.survey
        """
        pass

    @property
    def auto_display(self):
        return self._auto_display

    @auto_display.setter
    def auto_display(self, value):
        if type(value) is bool:
            self._auto_display = value

    def display(self):
        """display the form with header first and include row names
        """
        display(self._table)

    def __repr__(self):
        if self.auto_display:
            self.display()
        columns = ', '.join(list(self.col_names))
        if len(columns) > 64:
            columns = columns[:61]
            while ',' in columns[-2:]:
                columns = columns[:-1]
            columns += '...'
        return 'FrameEditor([{}] X {:2d} rows)'.format(columns, len(self.row_names))
