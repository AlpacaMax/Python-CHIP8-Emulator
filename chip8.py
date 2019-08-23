import pygame
import time
import sys
import random
import os

class Register:
    def __init__(self, bits):
        self.value = 0
        self.bits = bits
    
    '''
    def checkFlag(self):
        hexValue = hex(self.value)[2:]
        carryORborrow = False

        if self.value < 0:
            self.value = abs(self.value)
            carryORborrow = True

        if len(hexValue) > self.bits / 4:
            self.value = int(hexValue[-int(self.bits / 4):], 16)
            carryORborrow = True

        if carryORborrow:
            return 1
        return 0
    '''

    def checkCarry(self):
        hexValue = hex(self.value)[2:]

        if len(hexValue) > self.bits / 4:
            self.value = int(hexValue[-int(self.bits / 4):], 16)
            return 1
        
        return 0
    
    def checkBorrow(self):
        if self.value < 0:
            self.value = abs(self.value)
            return 0
        
        return 1
    
    def readValue(self):
        return hex(self.value)
    
    def setValue(self, value):
        self.value = value

class DelayTimer:
    def __init__(self):
        self.timer = 0
    
    def countDown(self):
        if self.timer > 0:
            self.timer -= 1

    def setTimer(self, value):
        self.timer = value
    
    def readTimer(self):
        return self.timer

class SoundTimer(DelayTimer):
    def __init__(self):
        DelayTimer.__init__(self)

    def beep(self):
        if self.timer > 1:
            os.system('play --no-show-progress --null --channels 1 synth %s triangle %f' % (self.timer / 60, 440))
            self.timer = 0

class Stack:
    def __init__(self):
        self.stack = []
    
    def push(self, value):
        self.stack.append(value)
    
    def pop(self):
        return self.stack.pop()

class Emulator:
    def __init__(self):
        self.Memory = []
        for i in range(0, 4096):
            self.Memory.append(0x0)

        fonts = [ 
        0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
        0x20, 0x60, 0x20, 0x20, 0x70, # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
        0x90, 0x90, 0xF0, 0x10, 0x10, # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
        0xF0, 0x10, 0x20, 0x40, 0x40, # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90, # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
        0xF0, 0x80, 0x80, 0x80, 0xF0, # C
        0xE0, 0x90, 0x90, 0x90, 0xE0, # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ]
        for i in range(len(fonts)):
            self.Memory[i] = fonts[i]

        self.Registers = []
        for i in range(16):
            self.Registers.append(Register(8))
        
        self.IRegister = Register(16)
        self.ProgramCounter = 0x200

        self.stack = Stack()

        self.delayTimer = DelayTimer()
        self.soundTimer = SoundTimer()
        pygame.time.set_timer(pygame.USEREVENT+1, int(1000 / 60))
        
        self.keys = []
        for i in range(0, 16):
            self.keys.append(False)
        self.keyDict = {
            49 : 1,
            50 : 2,
            51 : 3,
            52 : 0xc,
            113 : 4,
            119 : 5,
            101 : 6,
            114 : 0xd,
            97 : 7,
            115 : 8,
            100 : 9,
            102 : 0xe,
            122 : 0xa,
            120 : 0,
            99 : 0xb,
            118 : 0xf
        }

        self.grid = []
        for i in range(32):
            line = []
            for j in range(64):
                line.append(0)
            self.grid.append(line)
        self.emptyGrid = self.grid[:]
        self.zeroColor = [0, 0, 50]
        self.oneColor = [255, 255, 255]

        pygame.init()
        self.size = 10
        width = 64
        height = 32
        self.screen = pygame.display.set_mode([width * self.size, height * self.size])
        self.screen.fill(self.oneColor)
        pygame.display.flip()
    
    def execOpcode(self, opcode):
        #print(opcode)

        if opcode[0] == '0':

            if opcode[1] != '0':
                #0NNN

                print("ROM attempts to run RCA 1802 program at <0x" + opcode[1:] + '>')

            else:
                if opcode == '00e0':
                    #00E0
                    #disp_clear()
                    
                    self.clear()

                elif opcode == '00ee':
                    #00EE
                    #return;

                    self.ProgramCounter = self.stack.pop()
        
        elif opcode[0] == '1':
            #1NNN
            #goto NNN;

            self.ProgramCounter = int(opcode[1:], 16) - 2
        
        elif opcode[0] == '2':
            #2NNN
            #*(0xNNN)()

            self.stack.push(self.ProgramCounter)
            self.ProgramCounter = int(opcode[1:], 16) - 2
        
        elif opcode[0] == '3':
            #3XNN
            #if(Vx==NN)

            vNum = int(opcode[1], 16)
            targetNum = int(opcode[2:], 16)

            if self.Registers[vNum].value == targetNum:
                self.ProgramCounter += 2

        elif opcode[0] == '4':
            #4XNN
            #if(Vx!=NN)

            vNum = int(opcode[1], 16)
            targetNum = int(opcode[2:], 16)

            if self.Registers[vNum].value != targetNum:
                self.ProgramCounter += 2

        elif opcode[0] == '5':
            #5XY0
            #if(Vx==Vy)

            v1 = int(opcode[1], 16)
            v2 = int(opcode[2], 16)

            if self.Registers[v1].value == self.Registers[v2].value:
                self.ProgramCounter += 2

        elif opcode[0] == '6':
            #6XNN
            #Vx = NN

            vNum = int(opcode[1], 16)
            targetNum = int(opcode[2:], 16)

            self.Registers[vNum].value = targetNum
        
        elif opcode[0] == '7':
            #7XNN
            #Vx += NN

            vNum = int(opcode[1], 16)
            targetNum = int(opcode[2:], 16)

            self.Registers[vNum].value += targetNum
            self.Registers[vNum].checkCarry()
        
        elif opcode[0] == '8':
            if opcode[3] == '0':
                #8XY0
                #Vx=Vy

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value = self.Registers[v2].value
            
            elif opcode[3] == '1':
                #8XY1
                #Vx=Vx|Vy

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value = self.Registers[v1].value | self.Registers[v2].value
            
            elif opcode[3] == '2':
                #8XY2
                #Vx=Vx&Vy

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value = self.Registers[v1].value & self.Registers[v2].value
            
            elif opcode[3] == '3':
                #8XY3
                #Vx=Vx^Vy

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value = self.Registers[v1].value ^ self.Registers[v2].value
            
            elif opcode[3] == '4':
                #8XY4
                #Vx += Vy

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value += self.Registers[v2].value

                self.Registers[0xf].value = self.Registers[v1].checkCarry()
            
            elif opcode[3] == '5':
                #8XY5
                #Vx -= Vy

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value -= self.Registers[v2].value

                self.Registers[0xf].value = self.Registers[v1].checkBorrow()
            
            elif opcode[3] == '6':
                #8XY6
                #Vx>>1

                v1 = int(opcode[1], 16)
                leastBit = int(bin(self.Registers[v1].value)[-1])

                self.Registers[v1].value = self.Registers[v1].value >> 1
                self.Registers[0xf].value = leastBit
            
            elif opcode[3] == '7':
                #8XY7
                #Vx=Vy-Vx

                v1 = int(opcode[1], 16)
                v2 = int(opcode[2], 16)

                self.Registers[v1].value = self.Registers[v2].value - self.Registers[v1].value

                self.Registers[0xf].value = self.Registers[v1].checkBorrow()
            
            elif opcode[3] == 'e':
                #8XYE
                #Vx<<=1

                v1 = int(opcode[1], 16)
                mostBit = int(bin(self.Registers[v1].value)[2])

                self.Registers[v1].value = self.Registers[v1].value << 1
                self.Registers[0xf].value = mostBit
        
        elif opcode[0] == '9':
            #9XY0
            #if(Vx!=Vy)

            v1 = int(opcode[1], 16)
            v2 = int(opcode[2], 16)

            if self.Registers[v1].value != self.Registers[v2].value:
                self.ProgramCounter += 2
        
        elif opcode[0] == 'a':
            #ANNN
            #I = NNN

            addr = int(opcode[1:], 16)

            self.IRegister.value = addr
        
        elif opcode[0] == 'b':
            #BNNN
            #PC=V0+NNN

            addr = int(opcode[1:], 16)

            self.ProgramCounter = self.Registers[0].value + addr - 2
        
        elif opcode[0] == 'c':
            #CXNN
            #Vx=rand()&NN

            vNum = int(opcode[1], 16)
            targetNum = int(opcode[2:], 16)

            rand = random.randint(0, 255)

            self.Registers[vNum].value = targetNum & rand
        
        elif opcode[0] == 'd':
            #DXYN
            #draw(Vx,Vy,N)
            
            Vx = int(opcode[1], 16)
            Vy = int(opcode[2], 16)
            N  = int(opcode[3], 16)

            addr = self.IRegister.value
            sprite = self.Memory[addr: addr + N]

            for i in range(len(sprite)):
                if type(sprite[i]) == str:
                     sprite[i] = int(sprite[i], 16)

            if self.draw(self.Registers[Vx].value, self.Registers[Vy].value, sprite):
                self.Registers[0xf].value = 1
            else:
                self.Registers[0xf].value = 0
        
        elif opcode[0] == 'e':
            if opcode[2:] == '9e':
                #EX9E
                #if(key()==Vx)

                Vx = int(opcode[1], 16)
                key = self.Registers[Vx].value
                if self.keys[key]:
                    self.ProgramCounter += 2

            elif opcode[2:] == 'a1':
                #EXA1
                #if(key()!=Vx)

                Vx = int(opcode[1], 16)
                key = self.Registers[Vx].value
                if not self.keys[key]:
                    self.ProgramCounter += 2
        
        elif opcode[0] == 'f':
            if opcode[2:] == '07':
                #FX07
                #delay_timer(Vx)

                Vx = int(opcode[1], 16)
                self.Registers[Vx].value = self.delayTimer.readTimer()

            elif opcode[2:] == '0a':
                #FX0A
                #Vx = get_key()

                Vx = int(opcode[1], 16)
                key = None

                while True:
                    self.keyHandler()
                    isKeyDown = False

                    for i in range(len(self.keys)):
                        if self.keys[i]:
                            key = i
                            isKeyDown = True
                    
                    if isKeyDown:
                        break
                
                self.Registers[Vx].value = key
            
            elif opcode[2:] == '15':
                #FX15
                #delay_timer(Vx)

                Vx = int(opcode[1], 16)
                value = self.Registers[Vx].value

                self.delayTimer.setTimer(value)
            
            elif opcode[2:] == '18':
                #FX18
                #sound_timer(Vx)

                Vx = int(opcode[1], 16)
                value = self.Registers[Vx].value

                self.soundTimer.setTimer(value)
            
            elif opcode[2:] == '1e':
                #FX1E
                #I += Vx

                Vx = int(opcode[1], 16)
                self.IRegister.value += self.Registers[Vx].value
            
            elif opcode[2:] == '29':
                #FX29
                #I = sprite_addr[Vx]

                Vx = int(opcode[1], 16)
                value = self.Registers[Vx].value

                self.IRegister.value = value * 5
            
            elif opcode[2:] == '33':
                #FX33
                '''
                set_BCD(Vx);
                *(I+0)=BCD(3);
                *(I+1)=BCD(2);
                *(I+2)=BCD(1);
                '''

                Vx = int(opcode[1], 16)
                value = str(self.Registers[Vx].value)

                fillNum = 3 - len(value)
                value = '0' * fillNum + value

                for i in range(len(value)):
                    self.Memory[self.IRegister.value + i] = int(value[i])
            
            elif opcode[2:] == '55':
                #FX55
                #reg_dump(Vx, &I)

                Vx = int(opcode[1], 16)
                for i in range(0, Vx + 1):
                    self.Memory[self.IRegister.value + i] = self.Registers[i].value

            elif opcode[2:] == '65':
                #FX65
                #reg_load(Vx, &I)

                Vx = int(opcode[1], 16)
                for i in range(0, Vx + 1):
                    self.Registers[i].value = self.Memory[self.IRegister.value + i]

        self.ProgramCounter += 2

    def execution(self):
        index = self.ProgramCounter
        high = self.hexHandler(self.Memory[index])
        low = self.hexHandler(self.Memory[index + 1])

        opcode = high + low

        self.execOpcode(opcode)

    def draw(self, Vx, Vy, sprite):
        collision = False

        spriteBits = []
        for i in sprite:
            binary = bin(i)
            line = list(binary[2:])
            fillNum = 8 - len(line)
            line = ['0'] * fillNum + line

            spriteBits.append(line)
        
        '''
        for i in spriteBits:
            print(i)
        '''

        for i in range(len(spriteBits)):
            #line = ''
            for j in range(8):
                try:
                    if self.grid[Vy + i][Vx + j] == 1 and int(spriteBits[i][j]) == 1:
                        collision = True

                    self.grid[Vy + i][Vx + j] = self.grid[Vy + i][Vx + j] ^ int(spriteBits[i][j])
                    #line += str(int(spriteBits[i][j]))
                except:
                    continue

            #print(line)
        
        return collision
    
    def clear(self):
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                self.grid[i][j] = 0

    def readProg(self, filename):
        rom = self.convertProg(filename)
        
        offset = int('0x200', 16)
        for i in rom:
            self.Memory[offset] = i
            offset += 1
    
    def convertProg(self, filename):
        rom = []

        with open(filename, 'rb') as f:
            wholeProgram = f.read()

            for i in wholeProgram:
                opcode = i
                rom.append(opcode)
        
        return rom
    
    def hexHandler(self, Num):
        newHex = hex(Num)[2:]
        if len(newHex) == 1:
            newHex = '0' + newHex
        
        return newHex

    def keyHandler(self):
        '''
        Chip8       My Keys
        ---------   ---------
        1 2 3 C     1 2 3 4
        4 5 6 D     q w e r
        7 8 9 E     a s d f
        A 0 B F     z x c v
        '''

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.USEREVENT+1:
                self.delayTimer.countDown()

            elif event.type == pygame.KEYDOWN:
                try:
                    targetKey = self.keyDict[event.key]
                    self.keys[targetKey] = True

                except: pass

            elif event.type == pygame.KEYUP:
                try:
                    targetKey = self.keyDict[event.key]
                    self.keys[targetKey] = False

                except: pass

    def mainLoop(self):
        clock = pygame.time.Clock()

        while True:
            clock.tick(300)
            self.keyHandler()
            self.soundTimer.beep()
            self.execution()
            self.display()
    
    def display(self):
        for i in range(0, len(self.grid)):
            for j in range(0, len(self.grid[0])):
                cellColor = self.zeroColor

                if self.grid[i][j] == 1:
                    cellColor = self.oneColor
                
                pygame.draw.rect(self.screen, cellColor, [j * self.size, i * self.size, self.size, self.size], 0)
        
        pygame.display.flip()

chip8 = Emulator()
chip8.readProg(sys.argv[1])
chip8.mainLoop()