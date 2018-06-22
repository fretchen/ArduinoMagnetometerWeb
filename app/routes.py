from app import app, socketio
from app.forms import DisconnectForm, ConnectForm, SerialWaitForm, ReConnectForm, SerialWaitForm
from app.forms import UpdateSetpointForm, UpdateGainForm, UpdateIntegralForm, UpdateDifferentialForm
from app.models import SerialArduinoMonitor, serialmonitors

from app.thermocontrol.models import tempcontrols

import h5py
import git
import numpy as np
from flask import render_template, flash, redirect, url_for, session

import time

from flask_socketio import emit, disconnect

# for subplots
import numpy as np

@app.context_processor
def git_url():
    '''
    The main function for rendering the principal site.
    '''
    repo = git.Repo(search_parent_directories=True)
    add =repo.remote().url
    add_c = add.split('.git')[0];
    comm = repo.head.object.hexsha;
    return dict(git_url = add_c + '/tree/' + comm);

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    '''
    The main function for rendering the principal site.
    '''
    global tempcontrols

    n_tcs = len(tempcontrols);
    tc_props = [];
    for ii, arduino in enumerate(tempcontrols):
        # create also the name for the readout field of the temperature
        temp_field_str = 'read' + str(arduino.id);
        dict = {'name': arduino.name, 'id': arduino.id, 'port': arduino.serial.port,
        'active': arduino.connection_open(), 'setpoint': arduino.setpoint,
        'label': temp_field_str};
        tc_props.append(dict)

    global serialmonitors

    n_sm = len(serialmonitors);
    sm_props = [];
    for ii, arduino in enumerate(serialmonitors):
        # create also the name for the readout field of the temperature
        temp_field_str = 'read_sm' + str(arduino.id);
        dict = {'name': arduino.name, 'id': arduino.id, 'port': arduino.serial.port,
        'active': arduino.connection_open(), 'label': temp_field_str};
        sm_props.append(dict)

    return render_template('index.html',n_tcs = n_tcs, tempcontrols = tc_props,
    n_sm = n_sm, serialmonitors = sm_props);

@app.route('/start', methods=['POST'])
def start():

    cform = ReConnectForm()

    global tempcontrols;
    if tempcontrols:
        ssProto = tempcontrols[0];
    else:
        flash('No arduino connection existing yet', 'error')
        return redirect(url_for('add_tempcontrol'))

    if cform.validate_on_submit():
        try:
            ssProto.open_serial(app.config['SERIAL_PORT'], 9600, timeout = 1)
            ssProto.start()
            flash('Started the connection')
            return redirect(url_for('index'))
        except Exception as e:
            flash('{}'.format(e), 'error')
            return redirect(url_for('config'))

    return redirect(url_for('config'))

@app.route('/stop', methods=['POST'])
def stop():
    dform = DisconnectForm()
    global tempcontrols;
    if tempcontrols:
        ssProto = tempcontrols[0];
    else:
        flash('Nothing to disconnect from', 'error')

    if dform.validate_on_submit():
        #Disconnect the port.
        ssProto.stop()
        ssProto.serial.close()

        flash('Closed the serial connection')
        return redirect(url_for('config'))

    return redirect(url_for('config'))

@app.route('/file/<filestring>')
def file(filestring):
    '''function to save the values of the hdf5 file. It should have the following structure
    <ard_nr>+<filename>
    '''
    # first let us devide into the right parts
    print(filestring)
    parts = filestring.split('+');
    if not len(parts) == 2:
        flash('The filestring should be of the form')
        return redirect(url_for('index'))

    filename = parts[1]
    id = int(parts[0])

    global tempcontrols;

    if id >= len(tempcontrols):
        flash('Arduino Index out of range.')
        return redirect(url_for('index'))

    arduino = tempcontrols[id];
    # We should add the latest value of the database here. Better would be to trigger the readout.
    # Let us see how this actually works.
    vals = arduino.ard_str.split(',');
    if vals:
        with h5py.File(filename, "a") as f:
            if 'globals' in f.keys():
                params = f['globals']
                params.attrs['TSet'] = np.float(vals[0])
                params.attrs['TMeasure'] = np.float(vals[1])
                flash('Added the vals {} to the file {}'.format(arduino.ard_str, filename))
            else:
                flash('The file {} did not have the global group yet.'.format(filename), 'error')
    else:
        flash('Did not have any values to save', 'error')

    return render_template('file.html', file = filename, vals = vals)

# communication with the websocket
@socketio.on('connect')
def run_connect():
    '''
    we are connecting the client to the server. This will only work if the
    Arduino already has a serial connection
    '''
    socketio.emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('stop')
def run_disconnect():
    print('Should disconnect')

    session['receive_count'] = session.get('receive_count', 0) + 1

    global tempcontrols;
    # we should even kill the arduino properly.
    if tempcontrols:
        ssProto = tempcontrols[0];
        ser = ssProto.serial;
        ser.close();
        ssProto.stop();
        emit('my_response',
            {'data': 'Disconnected!', 'count': session['receive_count']})
    else:
        emit('my_response',
            {'data': 'Nothing to disconnect', 'count': session['receive_count']})

@socketio.on('my_ping')
def ping_pong():
    emit('my_pong')

############ The serial SerialArduinoMonitor stuff

@app.route('/add_serialmonitor', methods=['GET', 'POST'])
def add_serialmonitor():
    '''
    Add an arduino to the set up
    '''
    global serialmonitors;
    cform = ConnectForm();

    if cform.validate_on_submit():
        n_port =  cform.serial_port.data;
        name = cform.name.data;
        ssProto = SerialArduinoMonitor(socketio, name);
        ssProto.id = len(serialmonitors);
        try:
            ssProto.open_serial(n_port, 9600, timeout = 1)
            ssProto.start()
            if ssProto.is_open():
                app.config['SERIAL_PORT'] = n_port;
                serialmonitors.append(ssProto)
                flash('We added a new arduino {}'.format(app.config['SERIAL_PORT']))
                return redirect(url_for('index'))
            else:
                 flash('Adding the Arduino went wrong', 'error')
                 return redirect(url_for('add_serialmonitor'))
        except Exception as e:
             flash('{}'.format(e), 'error')
             return redirect(url_for('add_serialmonitor'))

    port = app.config['SERIAL_PORT']
    n_ards = len(serialmonitors)
    return render_template('add_arduino.html', port = port, cform = cform, n_ards=n_ards,
    device_type = 'serial monitor');
