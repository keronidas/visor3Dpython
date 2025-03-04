# ControladorPID

class ControladorPID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0
        self.integral = 0

    def reset_integral(self):
        self.integral = 0

    def compute(self, error):
        if error == 0:
            self.integral = 0
        self.integral += error 
        derivative = (error - self.prev_error) 
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative 
        self.prev_error = error

        
        print(f'Proporcional={self.Kp*error}, integral={self.Ki*self.integral}, derivativo={self.Kd*derivative}, output={output}')
        return output
