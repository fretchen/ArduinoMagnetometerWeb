from app import app, socketio
from app.forms import ConnectForm, DataForm
import serial
import h5py
from threading import Lock
from flask import render_template, flash, redirect, url_for, session
from flask_socketio import emit, disconnect

# for subplots
import numpy as np
from datetime import datetime

thread = None
thread_lock = Lock()

#create the dummy dataframed
fname = '';

def create_test_data():
    '''
    A function to create test data for plotting.
    '''
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat();
    Verr = np.random.randint(10);
    Vmeas = np.random.randint(750);
    Vinp = np.random.randint(50);
    d_str = timestamp + '\t' + str(Verr) + '\t' + str(Vmeas) + '\t' + str(Vinp);
    #d = {'timestamp': timestamp, 'Verr': Verr, 'Vmeas': Vmeas, 'Vinp': Vinp}
    return d_str

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    '''
    The main function for rendering the principal site.
    '''
    return render_template('index.html', async_mode=socketio.async_mode)

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
        return redirect(url_for('index'))

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

# communication with the websocket
def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        #session['receive_count'] = session.get('receive_count', 0) + 1
        count += 1
        data_str = create_test_data()

        socketio.emit('my_response',
                      {'data': data_str, 'count': count},
                      namespace='/test')

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')

@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    Vinp = np.random.randint(50);
    emit('my_response',
         {'data': Vinp, 'count': session['receive_count']})

# error handling
@app.errorhandler(500)
def internal_error(error):
    flash('An error occured {}'.format(error), 'error')
    return render_template('500.html'), 500
