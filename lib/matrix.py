#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# This file is part of PLACEMENT software
# PLACEMENT helps users to bind their processes to one or more cpu-cores
#
# PLACEMENT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  Copyright (C) 2015-2018 Emmanuel Courcelle
#  PLACEMENT is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with PLACEMENT.  If not, see <http://www.gnu.org/licenses/>.
#
#  Authors:
#        Emmanuel Courcelle - C.N.R.S. - UMS 3667 - CALMIP
#        Nicolas Renon - Université Paul Sabatier - University of Toulouse)
#

from exception import *
from utilities import *

#
# Réécrit le placement pour des ensembles de threads et de tâches
# Réécriture matricielle, une colonne par cœur et une ligne par thread
#
# Params: archi (l'architecture processeurs)
#         ppsr_min, ppsr_max = Les cœurs limites (physiques)
# Return: la chaine de caracteres pour affichage
#

class Matrix(object):
    """ Compute the placement in  matrix (1 col/core, 1 line/thread) for sets of running threads 
        This representation is used ONLY with the option --check, to check running jobs
    """

    def __init__(self,archi,ppsr_min=-1,ppsr_max=-1):
        """ Parameters: archi    = The object Architecture found
                        ppsr_min = The min used core number 
                        ppsr_max = The max used core number (useful if not all sockets are used by the job, as we do not draw all sockets)
        """
        self.__hard  = archi.hardware
        self.__archi = archi
        if ppsr_min < 0:
            self.__ppsr_min = 0
            self.__ppsr_max = archi.sockets_per_node * archi.cores_per_socket - 1
        else:
            # We correct ppsr_min and ppsr_max to sockets boundaries
            self.__socket_min = self.__hard.getCore2Socket(ppsr_min)
            self.__socket_max = self.__hard.getCore2Socket(ppsr_max)
            self.__ppsr_min = self.__hard.getSocket2CoreMin(self.__socket_min)
            self.__ppsr_max = self.__hard.getSocket2CoreMax(self.__socket_max)

        # Used by getLine
        self.__last_pid = 0
        self.__last_sid = 0

    def getHeader(self,h_header=15*' '):
        '''Return a header with psr nb displayed on 3 lines (must be < 999 !)'''

        self.__last_pid = 0
        rvl = ''

        # Ligne 1 = les centaines
        rvl += h_header
        for p in range(self.__ppsr_min,self.__ppsr_max+1):
            if self.__hard.getCore2Core(p)==0:
                rvl += ' '
            rvl += str(self.__hard.getCore2Addr(p)//100)
        rvl += '\n'

        # Ligne 2 = les dizaines
        rvl += h_header
        for p in range(self.__ppsr_min,self.__ppsr_max+1):
            if self.__hard.getCore2Core(p)==0:
                rvl += ' '
            rvl += str((self.__hard.getCore2Addr(p)%100)//10)
        rvl += '\n'

        # Ligne 3 = les unités
        rvl += h_header
        for p in range(self.__ppsr_min,self.__ppsr_max+1):
            if self.__hard.getCore2Core(p)==0:
                rvl += ' '
            rvl += str(self.__hard.getCore2Addr(p)%10)
#        rvl += '  %CPU %MEM'
        rvl += '\n'
        return rvl


    def getHeader1(self,h_header=15*' '):
        '''Return a header with left and right column labels'''

        self.__last_pid = 0
        rvl = '     PID    TID'

        # Skip columns
        n_cores   =  self.__ppsr_max-self.__ppsr_min+1
        n_sockets =  self.__socket_max-self.__socket_min+1
        n_blanks  =  n_cores + n_sockets
        rvl       += n_blanks*' '

        # Right column label
        rvl += '  %CPU %MEM  SESS\n'
        return rvl

    def getHeader2(self,jobsched=None,h_header=15*' '):
        '''Return a header with a point (unicode 9679) per psr, the color is related to the cpuset - ie to the jobid
           If jobsched is None, return ""'''

        if jobsched == None:
            return ''


        rvl = h_header
        for p in range(self.__ppsr_min,self.__ppsr_max+1):
            if self.__hard.getCore2Core(p)==0:
                rvl += ' '
            
            jobid  = jobsched.findJobFromCore(p)
            jobtag = jobsched.findTagFromJob(jobid)
            if jobtag == 0:
                rvl += ' '
            else:
                rvl   += AnsiCodes.map(jobtag)
                rvl   += chr(9679)

        rvl += '\n'
        rvl += AnsiCodes.normal();
        
        return rvl
		
    def getNumamem(self,sockets_mem):
        """ Return lines describing memory occupation of the sockets, sockets_mem describes the memory used per task and per socket 
            We show the memory occupation relative to each memory socket
        """
        mem_pid_socket = self.__getMemPidSocket(sockets_mem)

        h_header='   DISTRIBUTION of the MEMORY among the sockets '
        
        rvl =  h_header
        rvl += "\n"
        
        tags = list(mem_pid_socket.keys())
        if len(tags)>0:
            tags.sort()
            for tag in tags:
                val = mem_pid_socket[tag]
                
                # Print a line
                rvl += tag
                rvl += ' '*2 + self.__getMemTag(sockets_mem,tag) + ' '*6
                for v in val:
                    rvl += getGauge(v,self.__hard.CORES_PER_SOCKET)
                    rvl += ' '
                rvl += '  '
                for v in val:
                    rvl += str(v)
                    rvl += '%  '
                
                rvl += "\n"
        else:
            rvl += "    WARNING - NO INFORMATION COLLECTED - May be a PERMISSION problem ?"

        rvl += "\n"

        return rvl

    def __isGpuMine(self,g,tasks_binding):
        '''Return True if we find some process belonging to me in the gpu processes'''

        for p in g['PS']:
            if p[0] in tasks_binding.threads_bound:
                return True
        return False
		
    def getGpuInfo(self,tasks_binding, print_only_my_gpus):
        """ return a string, representing the status of the gpus connected to the sockets"""

        rvl = ""
        gpus_info = tasks_binding.gpus_info
        # print ("tasks_binding.pid = " + str(tasks_binding.pid))
        # print ("tasks_binding.threads_bound = " + str(tasks_binding.threads_bound))
        
        col_skipped = ''
        for s in gpus_info:
            for g in s:

                # If print_only_my_gpus: do not print a gpu if it is not affected to me !
                print_gpu = (not print_only_my_gpus) or self.__isGpuMine(g,tasks_binding)
                if print_gpu:
                    rvl += '  '
                    rvl += 'GPU ' + str(g['id']) + "\n"
                    rvl += 'USE             ' + col_skipped + getGauge(g['U'],self.__hard.CORES_PER_SOCKET,True,True) + ' ' + str(g['U']) + "%\n"
                    rvl += 'MEMORY          ' + col_skipped + getGauge(g['M'],self.__hard.CORES_PER_SOCKET,True,True) + ' ' + str(g['M']) + "%\n"
                    rvl += 'POWER           ' + col_skipped + getGauge(g['P'],self.__hard.CORES_PER_SOCKET,True,True) + ' ' + str(g['P']) + "%\n"
                    rvl += 'PROCESSES       ' + col_skipped
    
                    # Build and print the line "PROCESSES"
                    # A process may be seen by the gpu but not considered by placement
                    # because its cpu use is 0 - Exemple = Cuda mps
                    for p in g['PS']:
                        pid  = p[0];
                        if pid in tasks_binding.threads_bound:
                            prc  = tasks_binding.threads_bound[pid]
                            rvl += AnsiCodes.map(prc['jobtag'])
                            rvl += prc['tag']
                            rvl += AnsiCodes.normal()
                        else:
                            rvl += '.'
  
                    rvl += "\n"
    
                    # Build and print the line "USED MEMORY"
                    rvl += 'USED MEMORY     ' + col_skipped
                    for p in g['PS']:
                        pid = p[0]
                        mem = p[1];
                        if pid in tasks_binding.threads_bound:
                            prc  = tasks_binding.threads_bound[pid]
                            rvl += AnsiCodes.map(prc['jobtag'])
                            rvl += getGauge1(mem)
                            rvl += AnsiCodes.normal()
                        else:
                            rvl += ' '
                    rvl += "\n\n"
                
                else:
                    rvl += '  '
                    rvl += 'GPU ' + str(g['id']) + "\n"
                    rvl += AnsiCodes.red_foreground() + AnsiCodes.reverse() + "NOT USED BY THIS JOB" + AnsiCodes.normal() + "\n\n"
                    
            col_skipped += ' '*(self.__hard.CORES_PER_SOCKET+1)
                
        return rvl
        
    def __getMemTag(self,sockets_mem,tag):
        '''Return the total memory allocated by the process, formatted  (in Mb, Gb or Tb)'''
        
        # Compute the allocated memory for this process, in Mbytes
        abs_mem=0
        for s in sockets_mem:
            abs_mem += s[tag]
        unit='Mb'
        
        # Convert to Gb if relevant
        if abs_mem > 1000:
            abs_mem /= 1000
            unit='Gb'

        # Convert to Tb if relevant
        if abs_mem > 1000:
            abs_mem /= 1000
            unit='Tb'
        
        fmt = '{:5.1f}'
        return fmt.format(abs_mem) + unit

    def __getMemPidSocket(self,sockets_mem):
        """ Compute a NEW dict of arrays: 
                 - Key is a process tag
                 - Value is an array: 
                         the quantity of memory used per socket, in %/total memory used by the process
        """

        # Create and fill the processes dictionary with absolute values        
        processes = {}
        if len(sockets_mem)>0:
            mem_p_proc= {} # key = tag, val = the total mem used by this process
            for sm in sockets_mem:
                for tag,val in sm.items():
                    if not tag in processes:
                        processes[tag] = []
                    if not tag in mem_p_proc:
                        mem_p_proc[tag] = 0
                    processes[tag].append(val)
                    mem_p_proc[tag] += val
            
            for tag,val in processes.items():
                sum=0.0
                for x in val:
                    sum += x
                if sum!=0:
                    processes[tag] = [int(100.0*x/sum) for x in val]
                else:
                    processes[tag] = [0 for x in val]
                    
        return processes

    def getLine(self,pid,tid,ppsr,S,H,cpu=0,mem='-',sid=0):
        """ Return a line full of '.' and a letter on the psr coloumn, plus cpu occupation at end of line"""

        if (ppsr<self.__ppsr_min or ppsr>self.__ppsr_max):
            raise PlacementException("INTERNAL ERROR - psr ("+str(ppsr)+") should belong to ["+str(self.__ppsr_min)+','+str(self.__ppsr_max)+"]")

        space = "."
        fmt1  = '{:6d}'
        fmt2  = '{:5.1f}'
        pre = H[0] + ' '
        post= ''
        
        # NOTE - pid=0 means = Print an empty line, no process running !
                    
        # Print the pid only for the first thread
        if pid == 0 or pid != self.__last_pid:
            self.__last_pid = pid
            pre += fmt1.format(pid) + ' ' + fmt1.format(tid)
            # Print the tid only for the first process of the session
            if (sid != self.__last_sid):
                self.__last_sid = sid
                post = fmt1.format(sid)
            else:
                post = ''
        else:
            pre += 7 * ' ' + fmt1.format(tid)
            post = ''
        

        addr  = self.__hard.getAddr2Core(ppsr)
        socket= self.__hard.getCore2Socket(addr)
        core  = self.__hard.getCore2Core(addr)

        # Les colonnes vides avant le coeur concerne
        debut = self.__blankBeforeCore(socket,core)
        
        # Les colonnes vides après le coeur concerne
        fin   = self.__blankAfterCore(socket,core)

        # Les infos de %cpu et %mem
        cpumem = fmt2.format(cpu)
        if mem=='-':
            cpumem += '    -'
        else:
            cpumem += fmt2.format(mem)
            
        if pid==0:
            return pre + ' ' + debut + '.' + fin + cpumem + post + '\n'
        else:
            return pre + ' ' + debut + S + fin + cpumem + post + '\n'

    def __blankBeforeCore(self,socket,core):
        space = '.'
        bgn = ''
        for s in range(self.__socket_min,socket):
            bgn += self.__hard.CORES_PER_SOCKET * space
            bgn += ' '
        for c in range(0,core):
            bgn += space
        return bgn
        
    def __blankAfterCore(self,socket,core):
        space = '.'
        end   = ''
        for c in range(core+1,self.__hard.CORES_PER_SOCKET):
            end += space
        end += ' '
        for s in range(socket+1,self.__socket_max+1):
            end += self.__hard.CORES_PER_SOCKET * space
            end += ' '
        return end
