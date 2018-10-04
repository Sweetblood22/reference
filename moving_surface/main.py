import os
import numpy as np
from copy import copy
from json import load
from sklearn.preprocessing import MinMaxScaler
from bokeh.models.widgets import TextInput, Panel, Tabs, Button
from bokeh.models import (CustomJS, ColumnDataSource, Slider, Div, HoverTool, CrosshairTool, Div, ResetTool,
                          PrintfTickFormatter)
from bokeh import events
from bokeh.plotting import Figure, curdoc
from bokeh.layouts import gridplot, layout, Column, Row, widgetbox
from bokeh.models.tickers import BasicTicker
from surface3d import Surface3d

COL_WIDTH = 136
ROW_HEIGHT = 110
cwd = os.path.join(os.getcwd(), 'moving_surface')

features = ['avg_warhead_load',
            'weighted_avg_yld',
            'var_warhead_load',
            'probability_penetrate',
            'boost_reliability',
            'soa',
            'hob',
            'launch_reliability',
            'rb_reliability',
            'cep']
fnames = ['Average Warhead Load',
          'Weighted Average Yield',
          'Variance Warhead Load',
          'Probability Penetrate',
          'Boost Reliability',
          'Speed of Advance',
          'Height of Burst',
          'Launch Reliability',
          'Release Body Reliability',
          'Circular Error Probable']
vnames = ['avg_wh', 'yld', 'var_wh', 'pene', 'boost', 'soa', 'hob', 'launch', 'rb_r', 'cep']
response = ['missiles_expended', 'total_wh_expended']
rnames = ['Pred # Missiles', 'Pred # Warheads']
r_long_names = ['Predicted Number of Missiles Expended', 'Predicted Number of Warheads Expended']

with open(os.path.join(cwd, "feature_scales.json"), 'r') as f:
    psource = load(f)

psource = ColumnDataSource(psource['data'])

scalers = [MinMaxScaler().fit(np.array(psource.data[v + '_bnds']).reshape(2,1)) for v in vnames]

with open(os.path.join(cwd, "model_coefficients.json"), 'r') as f:
    coefsource = load(f)

coefsource = ColumnDataSource(coefsource['data'])


def r1_predict(X):
    c0 = np.array(coefsource.data['coef'][0][0])
    c1 = np.array(coefsource.data['coef'][0][1])
    b0 = np.array(coefsource.data['cept'][0][0])
    b1 = np.array(coefsource.data['cept'][0][1])
    return (np.tanh(X.dot(c0) + b0).dot(c1) + b1)[:, 0]


def r2_predict(X):
    c0 = np.array(coefsource.data['coef'][1][0])
    c1 = np.array(coefsource.data['coef'][1][1])
    b0 = np.array(coefsource.data['cept'][1][0])
    b1 = np.array(coefsource.data['cept'][1][1])
    return (np.tanh(X.dot(c0) + b0).dot(c1) + b1)[:, 0]


N = 64
xpts = np.array([psource.data[v + '_p'][0] for v in vnames])
xmeans = np.array([sc.inverse_transform(x)[0, 0] for x, sc in zip(xpts, scalers)]).reshape(1, 10)
mmpts = xpts * np.ones((N, 1))
x_ = np.linspace(0, 1, N)
xs = []
y1s = []
y2s = []
for i, (f, sc) in enumerate(zip(features, scalers)):
    x_f = sc.inverse_transform(x_.reshape(-1, 1))
    xs.append(x_f)
    xx = copy(mmpts)
    xx[:, i] = x_.ravel()
    y1_f = r1_predict(xx)
    y2_f = r2_predict(xx)
    y1s.append(y1_f)
    y2s.append(y2_f)
    
shortdata = {}
for key, ray in dict(y1=y1s, y2=y2s, x=xs).items():
    for i in range(len(ray)):
        shortdata[vnames[i] + '_' + key] = ray[i]
shortdata['x_'] = x_
shortdata['zeroes'] = x_ * 0

pdict = {'x': [0, 0],
         'y': [1, 1]}
r1val = r1_predict(np.vstack([xpts]*2))
r2val = r2_predict(np.vstack([xpts]*2))
pdict['r1val'] = r1val.tolist()
pdict['r2val'] = r2val.tolist()

for vn, xp, sc in zip(vnames, xpts, scalers):
    pdict[vn+'_p'] = [xp, xp]
    pdict[vn+'_bnds'] = [sc.data_min_[0], sc.data_max_[0]]

with open('C:\\Users\\jmccrary\\moving_surface\\moving_profiles_and_surface.js', 'r') as f:
    textcode = f.read() % ("'%s'", vnames)

x = np.linspace(0, 1, 25)
y = np.linspace(0, 1, 25)
wx, wy = np.meshgrid(x, y)
wx = wx.ravel()
wy = wy.ravel()
xx = scalers[0].inverse_transform(wx.reshape(1, -1)).reshape(len(wx))
yy = scalers[1].inverse_transform(wy.reshape(1, -1)).reshape(len(wy))
rr1 = r1_predict(np.vstack([wx, wy] + [np.ones(wx.shape) * xm for xm in xpts[2:]]).T)
rr2 = r2_predict(np.vstack([wx, wy] + [np.ones(wy.shape) * xm for xm in xpts[2:]]).T)

surfsource = ColumnDataSource(data=dict(x=xx, y=yy, r1=rr1, r2=rr2, wx=wx, wy=wy))

surface1 = Surface3d(x='x', y='y', z='r1', color='r1', data_source=surfsource)
surface1.options['width'] = str(COL_WIDTH * 5) + 'px'
surface2 = Surface3d(x='x', y='y', z='r2', color='r2', data_source=surfsource)
surface2.options['width'] = str(COL_WIDTH * 5) + 'px'
tab1 = Panel(child=surface1, title=r_long_names[0])
tab2 = Panel(child=surface2, title=r_long_names[1])


hover = HoverTool(tooltips=[("avg_wh", "$x"), ("r1", "@avg_wh_y1")], mode='vline', names=["r_surf"])

pargs = {'plot_width': COL_WIDTH, 'plot_height': ROW_HEIGHT, 'tools': 'wheel_zoom', 'toolbar_location': None}

outdiv = Div(width=COL_WIDTH * 11)

style = {'font-size': '1.25em',
         'text-align': 'center',
         'vertical-align': 'middle',
         'margin-top': 0}

inputstyle = {'margin-left': 10,
              'margin-right': 10}

source = ColumnDataSource(data=shortdata)
psource = ColumnDataSource(data=pdict)

t0_ps = []
textrow = []

for i in range(len(fnames)):
    t0_ps.append(Div(text=fnames[i], width=COL_WIDTH, height=40, style=style))
    val = pdict[vnames[i] + '_p'][0] \
          * (pdict[vnames[i] + '_bnds'][1] - pdict[vnames[i] + '_bnds'][0])\
          + pdict[vnames[i] + '_bnds'][0]
    textrow.append(TextInput(value='{:0.3f}'.format(val), title=None, width=COL_WIDTH + 32,
                             css_classes=['myTextInputFix']))
    callback = CustomJS(args=dict(psource=psource, source=source, coefsource=coefsource,
                                  surfsource=surfsource, outdiv=outdiv), code=textcode % vnames[i])
    textrow[-1].js_on_change('value', callback)

r1val = r1_predict(np.vstack([xpts]*2))

r1_ps = []
for i in range(len(vnames)):
    vn = vnames[i]
    if i == 0:
        r1_ps.append(figure(**pargs))
    else:
        r1_ps.append(figure(y_range=r1_ps[0].y_range, **pargs))
    r1_ps[-1].xaxis.visible = False
    r1_ps[-1].yaxis.visible = False
    r1_ps[-1].min_border = 0
    r1_ps[-1].line(x=vn + '_x', y=vn + '_y1', line_width=3, alpha=0.5, line_cap='round', name='r_surf', source=source)
    r1_ps[-1].line(vn+'_bnds', 'r1val', color='black', line_width=1, alpha=0.7, name='r_value', source=psource)
    # r1_ps[-1].toolbar.active_drag = r1_ps[-1].tools[??]
    r1_ps[-1].toolbar.active_scroll = r1_ps[-1].tools[0]
    hover = HoverTool(tooltips=[(vn, "$x"), ("r1", "@{}_y1".format(vn))], mode='vline', names=["r_surf"])
    r1_ps[-1].add_tools(hover)
    r1_ps[-1].grid.grid_line_alpha = 0.4
    callback = CustomJS(args=dict(myText=textrow[i]),
                        code="""myText.value = cb_obj['x'].toPrecision(5);""")
    r1_ps[-1].js_on_event(events.Tap, callback)
    r1_ps[-1].js_on_event(events.Pan, callback)

r2val = r2_predict(np.vstack([xpts]*2))
        
r2_ps = []
x_axes = []
axargs = {'plot_width': COL_WIDTH, 'plot_height': 24, 'tools': 'pan,wheel_zoom', 'toolbar_location': None}
for i in range(len(vnames)):
    vn = vnames[i]
    if i == 0:
        r2_ps.append(figure(x_range=r1_ps[i].x_range, **pargs))
    else:
        r2_ps.append(figure(y_range=r2_ps[0].y_range, x_range=r1_ps[i].x_range, **pargs))
    r2_ps[-1].yaxis.visible = False
    r2_ps[-1].xaxis.visible = False
    r2_ps[-1].min_border = 0
    r2_ps[-1].line(x=vn + '_x', y=vn + '_y2', line_width=3, alpha=0.5, line_cap='round', name='r_surf', source=source)
    r2_ps[-1].line(vn+'_bnds', 'r2val', color='black', line_width=1, alpha=0.7, name='r_value', source=psource)
    r2_ps[-1].toolbar.active_scroll = r2_ps[-1].tools[0]
    hover = HoverTool(tooltips=[(vn, "$x"), ("r2", "@{}_y2".format(vn))], mode='vline', names=['r_surf'])
    r2_ps[-1].add_tools(hover)
    r2_ps[-1].grid.grid_line_alpha = 0.4
    callback = CustomJS(args=dict(myText=textrow[i]),
                        code="""myText.value = cb_obj['x'].toPrecision(5);""")
    r2_ps[-1].js_on_event(events.Tap, callback)
    r2_ps[-1].js_on_event(events.Pan, callback)
    x_axes.append(Figure(x_range=r1_ps[i].x_range, **axargs))
    x_axes[-1].line(x=vn + '_x', y='zeroes', line_width=0.5, alpha=0.3, line_cap='round', source=source)
    x_axes[-1].yaxis.visible = False
    x_axes[-1].xgrid.visible = False
    x_axes[-1].ygrid.visible = False
    x_axes[-1].toolbar.active_scroll = x_axes[-1].tools[1]
    x_axes[-1].toolbar.active_drag = x_axes[-1].tools[0]
    x_axes[-1].min_border = 0
    x_axes[-1].xaxis.ticker = BasicTicker(desired_num_ticks=2)

# r2_ps[-1].toolbar.logo = None
resetter = ResetTool()
callback = CustomJS(code="""console.log('hello world')""", args={})
resetter.js_on_event('active', callback)
r2_ps[-1].add_tools(resetter)

pargs['plot_width'] = 53
pargs.pop('plot_height')
pargs['toolbar_location'] = None
pargs['tools'] = 'pan,wheel_zoom'
y_axes = [Figure(y_range=r1_ps[0].y_range, plot_height=ROW_HEIGHT, **pargs),
          Figure(y_range=r2_ps[0].y_range, plot_height=ROW_HEIGHT + axargs['plot_height'], **pargs)]
for i, y_ax in enumerate(y_axes):
    y_ax.xgrid.visible = False
    y_ax.ygrid.visible = False
    y_ax.xaxis.visible = False
    y_ax.min_border = 0
    y_ax.toolbar.active_scroll = y_ax.tools[1]
    # for some reason the following line totally breaks the profiler
    y_ax.yaxis[0].formatter = PrintfTickFormatter(format="%4d")
    y_ax.yaxis.axis_label = rnames[i]
    y_ax.line(x='zeroes', y='avg_wh_y' + str(i + 1),
              line_width=0.5, alpha=0.3, line_cap='round', source=source)

left_column = Column([Div(height=73, width=25)] + y_axes)

profile = Row([left_column] + [Column(ti, inp, r1, r2, x_ax,
                                      width=COL_WIDTH) for ti, inp, r1, r2, x_ax in zip(t0_ps,
                                                                                        textrow,
                                                                                        r1_ps,
                                                                                        r2_ps,
                                                                                        x_axes)])
surftab = Tabs(tabs=[tab1, tab2], width=COL_WIDTH * 5)

curdoc().add_root(Column(profile, surftab))
