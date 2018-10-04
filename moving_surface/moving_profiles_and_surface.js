var myName = %s;
var data = source.data;
var pdata = psource.data;
var sdata = surfsource.data;
var g = cb_obj.value;
var codat = coefsource.data;
var vnames = %s;

var aixs = new Array(vnames.length);
for (i = 0; i < vnames.length; i++) {
  aixs[i] = i;
};
var myix = vnames.indexOf(myName);
var oixs = aixs.slice();
oixs.splice(myix, 1);
var mixs = [];
var xzpt = [];
var newrval = 0;
var partval = 0;
var bnds = pdata[myName + '_bnds'].slice();
var newy = [];
var h = (g - bnds[0]) / (bnds[1] - bnds[0]);
var x_ = data['x_'].slice();
var partsums = []; 

// updated selected point data
pdata[myName + '_p'] = [h, h];

// scale the current point to minmax interval of [0, 1] for proper input into activations
for (i = 0; i < vnames.length; i++) {
  xzpt[i] = pdata[vnames[i] + '_p'][0] + 0;
};

for (r = 0; r < 2; r++) {

    var coef0 = codat['coef'][r][0]
    var coef1 = codat['coef'][r][1]
    var cept0 = codat['cept'][r][0]
    var cept1 = codat['cept'][r][1]

    //var line = "<span style=float:left;clear:left;font_size=0.5pt><b>CALC: " + myName + "</b> codat['coef'][0].length = " + codat['coef'][0].length + ", typeof(codat['coef'][0][0]) = " + typeof(codat['coef'][0][0]) + ", typeof(codat['coef'][0][1]) = " + typeof(codat['coef'][0][1]) + "</span>\\n";
    //var text = outdiv.text.concat(line);
    //var lines = text.split("\\n")
    //if ( lines.length > 350 ) { lines.shift(); }
    //outdiv.text = lines.join("\\n");

    newrval = 0 + cept1[0];
    for (j=0; j < coef0[0].length; j++) {
      partval = 0 + cept0[j];

      for (i=0; i < coef0.length; i++) {
        partval += coef0[i][j] * xzpt[i];
      };
      newrval += Math.tanh(partval) * coef1[j][0];

    };
    pdata['r' + (r+1) + 'val'] = [newrval, newrval];

    // update other features since current feature line won't change
    for (o = 0; o < oixs.length; o++) {
      newy = new Array(x_.length); // initialize array for new curve y values
      for (k = 0; k < x_.length; k++) {
        newy[k] = 0 + cept1[0]; // start with the output activation's intercept
      };
      mixs = aixs.slice(); // copy of indices
      mixs.splice(oixs[o], 1); // drop current feature's index

      // make a list of partial weighted sums of the mix features for input to
      // each perceptron so that we don't have to do these operations k times
      partsums = new Array(cept1.length);
      for (j = 0; j < cept0.length; j++) {
        partsums[j] = cept0[j] + 0; // start with each input activation's intercept
        // just add weighted static values to the partsums
        for (i = 0; i < mixs.length; i++) {
          partsums[j] += coef0[mixs[i]][j] * xzpt[mixs[i]];
        };
      };

      for (k = 0; k < x_.length; k++) {
        for (j = 0; j < coef0[oixs[o]].length; j++) {
          // add the weighted value of this feature's point
          newy[k] += Math.tanh(partsums[j] + coef0[oixs[o]][j] * x_[k]) * coef1[j][0];
        };
      };
      data[vnames[oixs[o]] + '_y' + (r+1)] = newy.slice();
    };
};

var selectedX = 0;
var selectedY = 1;

if (myix != selectedX & myix != selectedY ) {
  // only update other features since current feature line won't change
  var xx = sdata['wx'];
  var yy = sdata['wy'];
  mixs = aixs.slice(); // copy of indices
  // drop current surface features' indices
  if (selectedX == selectedY) {
  	mixs.splice(selectedX, 1);
  } else if (selectedX < selectedY) {
  	mixs.splice(selectedY, 1);
	mixs.splice(selectedX, 1);
  } else {
  	mixs.splice(selectedX, 1);
	mixs.splice(selectedY, 1);
  };
  for (r = 0; r < 2; r++) {
	
    var coef0 = codat['coef'][r][0]
    var coef1 = codat['coef'][r][1]
    var cept0 = codat['cept'][r][0]
    var cept1 = codat['cept'][r][1]

    //var line = "<span style=float:left;clear:left;font_size=0.5pt><b>CALC: " + myName + "</b> codat['coef'][0].length = " + codat['coef'][0].length + ", typeof(codat['coef'][0][0]) = " + typeof(codat['coef'][0][0]) + ", typeof(codat['coef'][0][1]) = " + typeof(codat['coef'][0][1]) + "</span>\\n";
    //var text = outdiv.text.concat(line);
    //var lines = text.split("\\n")
    //if ( lines.length > 350 ) { lines.shift(); }
    //outdiv.text = lines.join("\\n");

    newy = new Array(xx.length); // initialize array for new surface r values
    for (k = 0; k < xx.length; k++) {
      newy[k] = 0 + cept1[0]; // start with the output activation's intercept
    };

    // make a list of partial weighted sums of the mix features for input to
    // each perceptron so that we don't have to do these operations k times
    partsums = new Array(cept1.length);
    for (j = 0; j < cept0.length; j++) {
      partsums[j] = cept0[j] + 0; // start with each input activation's intercept
      // just add weighted static values to the partsums
      for (i = 0; i < mixs.length; i++) {
        partsums[j] += coef0[mixs[i]][j] * xzpt[mixs[i]];
      };
    };

    for (k = 0; k < xx.length; k++) {
      for (j = 0; j < coef0[selectedX].length; j++) {
        // add the weighted value of this feature's point
        newy[k] += Math.tanh(partsums[j] 
		                     + coef0[selectedX][j] * xx[k] 
		                     + coef0[selectedY][j] * yy[k]) * coef1[j][0];
      };
    };
    sdata['r' + (r+1)] = newy.slice();
  };
};


source.change.emit();
psource.change.emit();
surfsource.change.emit();

