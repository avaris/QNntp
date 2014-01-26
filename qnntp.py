import sip
sip.setapi('QString', 2)

from PyQt4 import QtGui, QtCore, QtNetwork


class QNntp(QtCore.QObject):
    readyResponse = QtCore.pyqtSignal(str)
    readyText = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    listReady = QtCore.pyqtSignal(list)
    groupReady = QtCore.pyqtSignal(int, int, int, str)
    listgroupReady = QtCore.pyqtSignal(list)
    statReady = QtCore.pyqtSignal(int, str)
    articleReady = QtCore.pyqtSignal(list, str)
    headReady = QtCore.pyqtSignal(list)
    bodyReady = QtCore.pyqtSignal(str)

    _longResponses = ('100',  # HELP
                      '101',  # CAPABILITIES
                      '211',  # LISTGROUP
                      '215',  # LIST
                      '220',  # ARTICLE
                      '221',  # HEAD
                      '222',  # BODY
                      '224',  # OVER
                      '225',  # HDR
                      '230',  # NEWNEWS
                      '231')  # NEWGROUPS

    def __init__(self, parent=None):
        super(QNntp, self).__init__(parent)

        # Internal socket object
        self._socket = QtNetwork.QTcpSocket()
        self._socket.readyRead.connect(self._socketRead)
        self._socket.connected.connect(self._socketConnected)
        self._socket.error.connect(self._socketError)

        # Internal: keeps the response for the current command
        self._data = ''
        self._host = None
        self._port = None
        self._connected = False
        self._lastError = ''
        # Internal: queue of commands (command, responseMethod, longResponse)
        self._queue = []
        self._welcome = ''
        self._postAllowed = False
        self._currentGroup = ''

    def connectToHost(self, host, port=119):
        '''
        Connect to host.

        Parameters
        ----------
        host : str
        port : int, optional
        '''
        self._queue = [('welcome', self._getWelcome, False)]
        self._socket.connectToHost(host, port)
        self._host = host
        self._port = port

    def _socketConnected(self):
        self._connected = True

    def _socketError(self, socketError):
        # handle socketError
        self._connected = False

    def _putCommand(self, cmd, method, longResponse):
        '''
        Internal: Sends the command to the server. Prepends the '\\r\\n'
        '''
        self._queue.append((cmd, method, longResponse))
        self._processCommands()

    def _processCommands(self):
        if self._queue:
            cmd = self._queue[0][0]
            self._socket.write('%s\r\n' % cmd)

    def _readResponse(self):
        '''
        Internal: Reads the last response and emits signals
        '''
        response, _, text = self._data.partition('\r\n')
        text = text.rstrip('\r\n.\r\n')
        command, method, longResponse = self._queue.pop(0)

        if response[0] not in '123':
            self._lastError = response
            self.error.emit(response)
            if command.startswith('GROUP '):
                self._currentGroup = ''
        else:
            self.readyResponse.emit(response)
            if text:
                self.readyText.emit(text)
            method(response, text)
        self._processCommands()

    def _socketRead(self):
        '''
        Internal: Reads data from socket until a response is completed. Then
        passes it to _readResponse
        '''
        self._data += str(self._socket.readAll())

        # all responses end with CRLF
        # wait for it
        if not self._data.endswith('\r\n'):
            return

        # check if we expect a long response
        if self._queue[0][2] and self._data[:3] in self._longResponses:
            # long response ends with CRLF.CRLF
            # wait for it
            if not self._data.endswith('\r\n.\r\n'):
                return

        # if we are here, we have a valid response
        self._readResponse()
        self._data = ''

    def _getWelcome(self, response, data):
        '''
        Internal: Read the welcome text and decide if posting is allowed.
        '''
        self._welcome = response
        if response.startswith('200'):
            self._postAllowed = True
        else:
            self._postAllowed = False

    def _getList(self, response, data):
        '''
        Internal: Process LIST [ACTIVE] command and emit listReady
        '''
        groups = [line.split() for line in data.splitlines()]
        self.listReady.emit(groups)

    def _getGroup(self, response, data):
        words = response.split()
        low = high = count = 0
        if len(words) > 1:
            count = int(words[1])
            if len(words) > 2:
                low = int(words[2])
                if len(words) > 3:
                    high = int(words[3])
                    if len(words) > 4:
                        self._currentGroup = words[4].lower()
        self.groupReady.emit(count, low, high, self._currentGroup)

    def _getListgroup(self, response, data):
        articles = [int(line) for line in data.splitlines()]
        self.listgroupReady.emit(articles)

    def _getStat(self, response, data):
        words = response.split()
        self.statReady.emit(int(words[1]), words[2])

    def _getArticle(self, response, data):
        headers, _, body = data.partition('\r\n\r\n')
        self.articleReady.emit(headers.splitlines(), body)

    def _getHead(self, response, data):
        self.headReady.emit(data.splitlines())

    def _getBody(self, response, data):
        self.bodyReady.emit(data)

    def list(self, pattern=''):
        '''
        Perform a ``LIST`` or ``LIST ACTIVE`` command.

        Parameters
        ----------
        pattern : str, optional

        Emits
        -----
        listReady : on success
        '''
        if pattern:
            cmd = 'LIST ACTIVE %s' % pattern
        else:
            cmd = 'LIST'
        self._putCommand(cmd, self._getList, True)

    def group(self, name):
        '''
        Perform a ``GROUP`` command.

        Parameters
        ----------
        name : str

        Emits
        -----
        groupReady : on success
        '''
        cmd = 'GROUP %s' % name
        self._currentGroup = name.lower()
        self._putCommand(cmd, self._getGroup, False)

    def listgroup(self, group=None, start=None, end=None):
        '''
        Perform a ``LISTGROUP`` command.

        Parameters
        ----------
        group : str, optional
        start : int, optional
        end : int, optional

        Emits
        -----
        listgroupReady : on success
        '''
        cmd = 'LISTGROUP'
        if group:
            cmd += ' %s' % group
            if start:
                cmd += ' %d-' % start
                if end:
                    cmd += '%d' % end
        self._putCommand(cmd, self._getListgroup, True)

    def stat(self, descriptor=''):
        '''
        Perform a ``STAT`` command.

        Parameters
        ----------
        descriptor : str, optional
            message-id or article number

        Emits
        -----
        statReady : on success

        See Also
        --------
        :meth:`next`
        :meth:`last`
        '''
        if descriptor:
            cmd = 'STAT %s' % descriptor
        else:
            cmd = 'STAT'
        self._putCommand(cmd, self._getStat, False)

    def next(self):
        '''
        Perform a ``NEXT`` command.

        Emits
        -----
        statReady : on success
        '''
        cmd = 'NEXT'
        self._putCommand(cmd, self._getStat, False)

    def last(self):
        '''
        Perform a ``LAST`` command.

        Emits
        -----
        statReady : on success
        '''
        cmd = 'LAST'
        self._putCommand(cmd, self._getStat, False)

    def article(self, descriptor=''):
        '''
        Perform an ``ARTICLE`` command.

        Parameters
        ----------
        descriptor : str, optional
            message-id or article number

        Emits
        -----
        articleReady : on success
        '''
        if descriptor:
            cmd = 'ARTICLE %s' % descriptor
        else:
            cmd = 'ARTICLE'
        self._putCommand(cmd, self._getArticle, True)

    def head(self, descriptor=''):
        '''
        Perform a ``HEAD`` command.

        Parameters
        ----------
        descriptor : str, optional
            message-id or article number

        Emits
        -----
        headReady : on success
        '''
        if descriptor:
            cmd = 'HEAD %s' % descriptor
        else:
            cmd = 'HEAD'
        self._putCommand(cmd, self._getHead, True)

    def body(self, descriptor=''):
        '''
        Perform a ``BODY`` command.

        Parameters
        ----------
        descriptor : str, optional
            message-id or article number

        Emits
        -----
        bodyReady : on success
        '''
        if descriptor:
            cmd = 'BODY %s' % descriptor
        else:
            cmd = 'BODY'
        self._putCommand(cmd, self._getBody, True)


class Dialog(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)

        self.nntp = QNntp()
        self.nntp.connectToHost('127.0.0.1')

        self.param1 = QtGui.QLineEdit()
        self.param2 = QtGui.QLineEdit()
        self.param3 = QtGui.QLineEdit()
        self.cmd = QtGui.QComboBox()
        self.process = QtGui.QPushButton('Process')
        self.process.clicked.connect(self.doCommand)

        self.response = QtGui.QLineEdit()
        self.error = QtGui.QLineEdit()
        self.data = QtGui.QTextBrowser()

        cmdLayout = QtGui.QHBoxLayout()
        cmdLayout.addWidget(self.param1)
        cmdLayout.addWidget(self.param2)
        cmdLayout.addWidget(self.param3)
        cmdLayout.addWidget(self.cmd)
        cmdLayout.addWidget(self.process)

        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(cmdLayout)
        layout.addWidget(self.response)
        layout.addWidget(self.data)
        layout.addWidget(self.error)

        self.nntp.readyResponse.connect(self.response.setText)
        self.nntp.error.connect(self.error.setText)

        self.setupCommands()

    def setupCommands(self):
        self.commands = [('LIST', self.list, self.nntp.listReady),
                         ('LISTGROUP', self.listgroup, self.nntp.listgroupReady),
                         ('GROUP', self.group, self.nntp.groupReady),
                         ('STAT', self.stat, self.nntp.statReady),
                         ('NEXT', self.next, self.nntp.statReady),
                         ('LAST', self.last, self.nntp.statReady),
                         ('ARTICLE', self.article, self.nntp.articleReady),
                         ('HEAD', self.head, self.nntp.headReady),
                         ('BODY', self.body, self.nntp.bodyReady)]

        for cmd, method, signal in self.commands:
            self.cmd.addItem(cmd)
            signal.connect(self.processResponse)

    def doCommand(self):
        self.commands[self.cmd.currentIndex()][1]()

    def processResponse(self, *data):
        if isinstance(data[0], list):
            self.data.setText('\n'.join(map(unicode, data[0])))
        else:
            self.data.setText(' | '.join(map(unicode, data)))

    def list(self):
        self.nntp.list(self.param1.text())

    def listgroup(self):
        group = self.param1.text()
        start = int(self.param2.text()) if self.param2.text() else None
        end = int(self.param3.text()) if self.param3.text() else None
        self.nntp.listgroup(group, start, end)

    def group(self):
        self.nntp.group(self.param1.text())

    def stat(self):
        self.nntp.stat(self.param1.text())

    def next(self):
        self.nntp.next()

    def last(self):
        self.nntp.last()

    def article(self):
        self.nntp.article(self.param1.text())

    def head(self):
        self.nntp.head(self.param1.text())

    def body(self):
        self.nntp.body(self.param1.text())


if __name__ == '__main__':
    app = QtGui.QApplication([])

    n = Dialog()
    n.show()

    app.exec_()
