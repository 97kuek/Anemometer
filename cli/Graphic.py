import curses

class Graphic():
    stdscr=curses.initscr()
    curses.cbreak()
    curses.noecho()
    curses.start_color()
    curses.init_pair(1,curses.COLOR_BLACK,curses.COLOR_GREEN)
    curses.init_pair(2,curses.COLOR_WHITE,curses.COLOR_RED)
    height,width = stdscr.getmaxyx()

    def MakeWindow(self):
        for h in range(self.height-2):
            self.stdscr.addstr(h,39,'|')

        for w in range(self.width-40):
            self.stdscr.addstr(5,40+w,'_')
    
    def BottomMessege(self):
        self.stdscr.addstr(self.height-2,0,"Press Ctrl + C to interrrupt")        

    def refresh(self):
        self.MakeWindow()
        self.BottomMessege()
        self.stdscr.refresh()

            
