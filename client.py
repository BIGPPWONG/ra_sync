#! /usr/bin/python
import socket
import os
import struct
import difflib

class client:
  cfilelist=[]
  cdirlist=[]
  sfilelist=[]
  sdirlist=[]
  s_only=[]
  c_only=[]
  sc_both=[]
  def __init__(self,dir,url,port):
    self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    self.sock.connect((url,port))
    self.dir=dir
    self.gen(dir=self.dir)

  def gen(self,dir,subdir=''):
    for file in os.listdir(dir):
      if os.path.isdir(os.path.join(dir,file)):
        self.cdirlist.append(os.path.join(subdir,file))
        self.gen(os.path.join(dir,file),os.path.join(subdir,file))
      else:
        self.cfilelist.append(os.path.join(subdir,file))
  
  def send_file(self,file):
    mtime=os.path.getmtime(file)
    self.send_msg(str(mtime))
    fp=open(file,'rb')
    data=fp.read()
    fp.close()
    self.send_msg(data)
    return len(data)
  
  def recv_file(self,file):
    mtime=eval(self.recv_msg())
    data=self.recv_msg()
    fp=open(file,'wb')
    fp.write(data)
    fp.close()
    os.utime(file,(mtime,mtime))
    return len(data)

  def diff(self):
    diff=difflib.Differ()
    d=diff.compare(self.cfilelist,self.sfilelist)
    l=list(d)
    for file in l:
      if file.startswith('+'):
        self.s_only.append(file[2:])
      elif file.startswith('-'):
        self.c_only.append(file[2:])
      else:
        self.sc_both.append(file[2:])

  def start(self):
    self.sfilelist=self.recv_msg()
    self.sfilelist=eval(self.sfilelist)
    print 'got sfilelist'
    self.send_msg('OK')

    self.sdirlist=self.recv_msg()
    self.sdirlist=eval(self.sdirlist)
    print 'got sdirlist'
    self.send_msg('OK')

    self.diff()

    for dir in self.sdirlist:
      try:
        os.mkdir(os.path.join(self.dir,dir))
      except:
        pass
#        print "Directory already exists: "+dir

    print '\nStart receiving Server_Only files...'
    i=0
    total_len=0
    while self.recv_msg()=='READY':
      try:
        file=self.s_only[i]
        i+=1
      except:
        self.send_msg('FINISH')
        print 'All Server_only files have been received.'
        print 'Total_len:',total_len
        break
      self.send_msg(file)
      total_len+=self.recv_file(os.path.join(self.dir,file))

    print '\nStart sending Client_Only  files to server...'
    i=0
    total_len=0
    while self.recv_msg()=='READY':
      try:
        file=self.c_only[i]
        i+=1
      except:
        self.send_msg('FINISH')
        print 'All Client_only files have been sent.'
        print 'Total_len:',total_len
        break
      self.send_msg(file)
      total_len+=self.send_file(os.path.join(self.dir,file))

    print '\nStart processing Server_Client_Both_Exist files.'
    print 'Olders will be replaced by newers.'
    i=0
    sendby_s=[]
    sendby_c=[]
    while self.recv_msg()=='READY':
      try:
        file=self.sc_both[i]
        i+=1
      except:
        self.send_msg('FINISH')
        print 'Comparion finished.'
        print 'Total compared files:',i
        break
      self.send_msg(file)
      s_mtime=self.recv_msg()
      s_mtime=eval(s_mtime)
      c_mtime=os.path.getmtime(os.path.join(self.dir,file))
      if int(s_mtime)>int(c_mtime):
        sendby_s.append(file)
      elif int(s_mtime)<int(c_mtime):
        sendby_c.append(file)
      else:
        pass 

    print '\nStart sending client files(newer)...'
    i=0
    total_len=0
    while self.recv_msg()=='READY':
      try:
        file=sendby_c[i]
        i+=1
        print file
      except:
        self.send_msg('FINISH')
        print 'Finish sending newer files to server.'
        print 'Send %s files. Total_len: %s'%(i,total_len)
        break
      self.send_msg(file)
      total_len+=self.send_file(os.path.join(self.dir,file))

    print '\nStart receiving server files...'
    i=0
    total_len=0
    while self.recv_msg()=='READY':
      try:
        file=sendby_s[i]
        i+=1
        print file
      except:
        self.send_msg('FINISH')
        print 'Finish receiving newer files from server.'
        print 'Total_len:',total_len
        break
      self.send_msg(file)
      total_len+=self.recv_file(os.path.join(self.dir,file))
    self.sock.close()

  def send_msg(self,data):
    data=struct.pack('>I',len(data))+data
    num=self.sock.sendall(data)
    return num
 
  def recv_msg(self):
    length=self.recv_all(4)
    length=struct.unpack('>I',length)[0]
    data=self.recv_all(length)
    return data

  def recv_all(self,length):
    data=''
    while len(data)<length:
      data+=self.sock.recv(length-len(data))
    return data


if __name__=='__main__':
  client=client('/root/python/pan','127.0.0.1',2000)
  client.start()
