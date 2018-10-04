// This file contains the JavaScript (CoffeeScript) implementation
// for a Bokeh custom extension. The "surface3d.py" contains the
// python counterpart.

// This custom model wraps one part of the third-party vis.js library:

//     http://visjs.org/index.html

// Making it easy to hook up python data analytics tools (NumPy, SciPy,
// Pandas, etc.) to web presentations using the Bokeh server.
var OPTIONS;

import * as p from "core/properties";

import {
  LayoutDOM,
  LayoutDOMView
} from "models/layouts/layout_dom";

// This defines some default options for the Graph3d feature of vis.js
// See: http://visjs.org/graph3d_examples.html for more details. This
// JS object should match the Python default value.
OPTIONS = {
  width: '640px',
  height: '480px',
  style: 'surface',
  showPerspective: false,
  showGrid: true,
  keepAspectRatio: false,
  showShadow: false,
  verticalRatio: 1.0,
  legendLabel: 'stuff',
  cameraPosition: {
    horizontal: -0.35,
    vertical: 0.22,
    distance: 1.8
  }
};

// To create custom model extensions that will render on to the HTML canvas
// or into the DOM, we must create a View subclass for the model. Currently
// Bokeh models and views are based on BackBone. More information about
// using Backbone can be found here:

//     http://backbonejs.org/

// In this case we will subclass from the existing BokehJS ``LayoutDOMView``,
// corresponding to our
export var Surface3dView = class Surface3dView extends LayoutDOMView {
  initialize(options) {
    super.initialize(options);
    // Create a new Graph3s using the vis.js API. This assumes the vis.js has
    // already been loaded (e.g. in a custom app template). In the future Bokeh
    // models will be able to specify and load external scripts automatically.

    // Backbone Views create <div> elements by default, accessible as @el. Many
    // Bokeh views ignore this default <div>, and instead do things like draw
    // to the HTML canvas. In this case though, we use the <div> to attach a
    // Graph3d to the DOM.
    this._graph = new vis.Graph3d(this.el, this.get_data(), this.model.options);
    // Set Backbone listener so that when the Bokeh data source has a change
    // event, we can process the new data
    return this.connect(this.model.data_source.change, () => {
      return this._graph.setData(this.get_data());
    });
  }

  // This is the callback executed when the Bokeh data has an change (e.g. when
  // the server updates the data). It's basic function is simply to adapt the
  // Bokeh data source to the vis.js DataSet format
  get_data() {
    var data, i, j, ref, source;
    data = new vis.DataSet();
    source = this.model.data_source;
    for (i = j = 0, ref = source.get_length(); 0 <= ref ? j < ref : j > ref; i = 0 <= ref ? ++j : --j) {
      data.add({
        x: source.get_column(this.model.x)[i],
        y: source.get_column(this.model.y)[i],
        z: source.get_column(this.model.z)[i],
        style: source.get_column(this.model.color)[i]
      });
    }
    return data;
  }

};

export var Surface3d = (function() {
  // We must also create a corresponding JavaScript Backbone model sublcass to
  // correspond to the python Bokeh model subclass. In this case, since we want
  // an element that can position itself in the DOM according to a Bokeh layout,
  // we subclass from ``LayoutDOM.model``
  class Surface3d extends LayoutDOM {};

  // This is usually boilerplate. In some cases there may not be a view.
  Surface3d.prototype.default_view = Surface3dView;

  // The ``type`` class attribute should generally match exactly the name
  // of the corresponding Python class.
  Surface3d.prototype.type = "Surface3d";

  // The @define block adds corresponding "properties" to the JS model. These
  // should basically line up 1-1 with the Python model class. Most property
  // types have counterparts, e.g. ``bokeh.core.properties.String`` will be
  // ``p.String`` in the JS implementatin. Where the JS type system is not yet
  // as rich, you can use ``p.Any`` as a "wildcard" property type.
  Surface3d.define({
    x: [p.String],
    y: [p.String],
    z: [p.String],
    color: [p.String],
    data_source: [p.Instance],
    options: [p.Any, OPTIONS]
  });

  return Surface3d;

})();