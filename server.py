#! /usr/bin/python
import os
import socket
import struct

class server:
  sfilelist=[]
  sdirlist=[]

  def __init__(self,dir,port):
    self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    self.sock.bind(('0.0.0.0',port))
    self.sock.listen(5)
    self.dir=dir
    self.gen(dir=self.dir)

  def gen(self,dir,subdir=''):
    for file in os.listdir(dir):
      if os.path.isdir(os.path.join(dir,file)):
        self.sdirlist.append(os.path.join(subdir,file))
        self.gen(os.path.join(dir,file),os.path.join(subdir,file))
      else:
        self.sfilelist.append(os.path.join(subdir,file))

  def send_file(self,file,connection):
    mtime=os.path.getmtime(file)
    self.send_msg(connection,str(mtime))
    fp=open(file,'rb')
    data=fp.read()
    fp.close()
    self.send_msg(connection,data)
    return len(data)

  def recv_file(self,file,connection):
    mtime=eval(self.recv_msg(connection))
    data=self.recv_msg(connection)
    fp=open(file,'wb')
    fp.write(data)
    fp.close()
    os.utime(file,(mtime,mtime))
    return len(data)

  def start(self):
    print 'Server started.'
    connection,address=self.sock.accept()
    print 'Connection established.'
    self.send_msg(connection,str(self.sfilelist))
    if self.recv_msg(connection)=='OK':
      print 'Sent filelist.'
    else:
      print 'Sending filelist fail.'
      return 1

    self.send_msg(connection,str(self.sdirlist))
    if self.recv_msg(connection)=='OK':
      print 'Sent dirlist.'
    else:
      print 'Sending dirlist fail.'
      return 1

#Begin SYNC
    print '\nStart sending Server_Only files to client...'
    self.send_msg(connection,'READY')
    next=self.recv_msg(connection)
    total_len=0
    while next!='FINISH':
      print next
      total_len+=self.send_file(os.path.join(self.dir,next),connection)
      self.send_msg(connection,'READY')
      next=self.recv_msg(connection)
    print 'All files have been sent. Total_len:',total_len

    print '\nStart receiving Client_Only  files...'
    self.send_msg(connection,'READY')
    next=self.recv_msg(connection)
    total_len=0
    while next!='FINISH':
      total_len+=self.recv_file(os.path.join(self.dir,next),connection)
      self.send_msg(connection,'READY')
      next=self.recv_msg(connection)
    print 'All Client files have been received. Total_len:',total_len   
    
    print '\nStart processing Server_Client_Both_Exist files...'
    print 'Olders will be replaced by newers.'
    print '\nStart comparasion...'
    self.send_msg(connection,'READY')
    next=self.recv_msg(connection)
    i=0
    while next!='FINISH':
      mtime=os.path.getmtime(os.path.join(self.dir,next))
      self.send_msg(connection,str(mtime))
      self.send_msg(connection,'READY')
      next=self.recv_msg(connection)
      i+=1
    print 'Finish comparasion. Total_files:',i   

    print '\nStart update newer files from client...'
    self.send_msg(connection,'READY')
    next=self.recv_msg(connection)
    total_len=0
    while next!='FINISH':
      print next
      total_len+=self.recv_file(os.path.join(self.dir,next),connection)
      self.send_msg(connection,'READY')
      next=self.recv_msg(connection)
    print 'Finish update. Total_len:',total_len

    print '\nStart sending newer files to client...'
    self.send_msg(connection,'READY')
    next=self.recv_msg(connection)
    total_len=0
    while next!='FINISH':
      total_len+=self.send_file(os.path.join(self.dir,next),connection)
      self.send_msg(connection,'READY')
      next=self.recv_msg(connection)
    print 'Finish. Total_len:',total_len

    connection.close()
    self.start()

  def send_msg(self,sock,data):
    length=len(data)
    data=struct.pack('>I',length)+data
    num=sock.sendall(data)
    return num
  
  def recv_msg(self,sock):
    length=self.recv_all(sock,4)
    length=struct.unpack('>I',length)[0]
    data=self.recv_all(sock,length)
    return data

  def recv_all(self,sock,length):
    data=''
    while len(data)<length:
      data+=sock.recv(length-len(data))
    return data
 
if __name__=='__main__':
  server=server('/root/pan',2000)
  server.start()
#  print server.filelist
#  print server.dirlist
