from app import app
from app.forms import ConnectForm, DataForm
import serial
import h5py
from flask import render_template, flash, redirect, send_file

# for subplots
from io import BytesIO
import base64
import numpy as np
import matplotlib as mpl
import pandas as pd
from datetime import datetime
mpl.use('AGG')

import matplotlib.pyplot as plt

#create the dummy dataframed
d = {'timestamp':[], 'Verr':[], 'Vmeas':[], 'Vinp':[]}
df = pd.DataFrame(d);
fname = '';

def create_test_data():
    timestamp = datetime.utcnow()
    Verr = np.random.randint(10);
    Vmeas = np.random.randint(750);
    Vinp = np.random.randint(50);
    d = {'timestamp': timestamp, 'Verr': Verr, 'Vmeas': Vmeas, 'Vinp': Vinp}
    return d

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    # test the data form
    dform = DataForm()
    if dform.validate_on_submit():
        #the following note is horrible and should be changed !!!!!
        global df
        df = df.append(create_test_data(), ignore_index = True);
        flash('We would like to submit some data locally. We have here {}'.format(df))
        flash('We would like to submit some data remote. We have here {}'.format(app.config['REMOTE_FILE']))
        return redirect('/index')

    # this could now actually become the last hundred lines of the dataframe.
    lyseout = 'This is some dummy output from lyse.'
    return render_template('index.html', lyseout=fname, dform = dform)

@app.route('/config', methods=['GET', 'POST'])
def config():
    port = app.config['SERIAL_PORT']
    form = ConnectForm()

    if form.validate_on_submit():

        app.config['SERIAL_PORT'] = form.serial_port.data
        flash('We set the serial port to {}'.format(app.config['SERIAL_PORT']))
        try:
            ser = serial.Serial(form.serial_port.data, 9600, timeout = 1)
        # except serial.SerialException:
        #     s.close()
        #     ser.close()
        #     ser = serial.Serial('COM32', 9600, timeout = 1)
        except Exception as e:
             flash('{}'.format(e), 'error')
        return redirect('/index')

    return render_template('config.html', port = port, form=form)

@app.route('/file/<filename>')
def file(filename):
    '''function to save the values of the hdf5 file'''

    # We should add the latest value of the database here. Better would be to trigger the readout.
    # Let us see how this actually works.
    vals = [1, 2, 3];
    with h5py.File(filename, "a") as f:
        if 'globals' in f.keys():
            params = f['globals']
            params.attrs['T_Verr'] = vals[0]
            params.attrs['T_Vmeas'] = vals[1]
            params.attrs['T_Vinp'] = vals[2]
            flash('The added vals to the file {}'.format(filename))
        else:
            flash('The file {} did not have the global group yet.'.format(filename), 'error')
    return render_template('file.html', file = filename)

@app.route('/fig')
def htmlplot():
    # make the figure
    #t = np.linspace(0,2*np.pi,100);
    t = df['timestamp'];
    y = df['Verr'];
    f, ax = plt.subplots()
    ax.plot(t,y)
    #df.plot(ax=ax)
    figfile = BytesIO()
    f.savefig(figfile);
    figfile.seek(0)
    return send_file(figfile, mimetype='image/png')

@app.route("/chartData/<entries>")
def chartData(entries):

    # Return the result with JSON format
    return df.to_json()

@app.errorhandler(500)
def internal_error(error):
    flash('An error occured {}'.format(error), 'error')
    return render_template('500.html'), 500
