import os
import eventlet
cameras = [];

class GuppySocketProtocol(object):
    '''
    A class which combines the serial connection and the socket into a single
    class, such that we can handle these things more properly.
    '''

    switch = False
    unit_of_work = 0
    name = '';
    id = 0;
    ard_str = '';
    folder = '.';
    xMin = 207; xMax = 597;yMin = 200; yMax = 500;

    def __init__(self, socketio, folder):
        """
        assign socketio object to emit
        add the folder to watch
        """
        if os.path.isdir(folder):
            self.folder = folder;
        else:
            print('Folder does not exist yet.')
            # TODO: Send back an error.
        self.socketio = socketio

    def __init__(self, socketio, folder, name):
        """
        as above, but also assign a name.
        """
        if os.path.isdir(folder):
            self.folder = folder;
        else:
            print('Folder does not exist yet.')
            # TODO: Send back an error.
        self.socketio = socketio;
        self.name = name;

    def is_open(self):
        '''
        test if the worker is running
        '''
        return self.switch

    def stop(self):
        """
        stop the loop and later also the serial port
        """
        self.unit_of_work = 0
        if self.is_open():
            self.serial.close()

    def start(self):
        """
        start to listen to the serial port of the Arduino
        """
        print('Starting the listener.')
        if not self.switch:
            self.switch = True
            thread = self.socketio.start_background_task(target=self.do_work)
        else:
            print('Already running')

    def do_work(self):
        """
        do work and emit message
        """

        previous_img_files = set()
        while self.switch:
            img_files = set(os.path.join(self.folder, f) for f in os.listdir(self.folder) if f.endswith('.BMP'))
            new_img_files = img_files.difference(previous_img_files)
            if new_img_files:
                self.unit_of_work += 1
                timestamp = datetime.now().replace(microsecond=0).isoformat();
                for img_file in new_img_files:
                    n_img = imageio.imread(img_file);

                    im_crop = n_img[self.yMin:self.yMax,self.xMin:self.xMax];
                    Nat = int(im_crop.sum());
                    print(Nat)
                self.socketio.emit('log_response',
                    {'time':timestamp, 'data': n_img.tolist(), 'count': self.unit_of_work,
                    'id': self.id, 'Nat': Nat})

                previous_img_files = img_files;


            eventlet.sleep(0.1)

    def trig_measurement(self):
        '''
        Creating a test pattern in the save_folder.
        '''
        # only read out on ask
        Nx = 752;
        Ny = 578;
        sigma = 20;
        xlin = np.linspace(0,Nx, Nx) - Nx/2;
        ylin = np.linspace(0,Ny, Ny) - Ny/2;
        [X, Y] = np.meshgrid(xlin,ylin);
        z = 255*np.exp(-(X**2 +Y**2)/sigma**2);

        z_int = z.astype('uint8')
        index = np.random.randint(100);
        name = self.folder + '/test' + str(index) + '.BMP';
        print(name)
        imageio.imwrite(name, z_int);

    def pull_data(self):
        '''
        Pulling the actual data from the guppy folder.
        '''
        return timestamp, self.ard_str
