#! /usr/bin/python
#FIXME consistent function names

class units():
	def __init__(self):
		pass

	def convert(self, value, target_unit):
		conversions = { "F" : self.temp_to_F(value),
		                "K" : self.temp_to_K(value),
		                "kmh" : self.ms_to_kmh(value),
		                "mph" : self.ms_to_mph(value),
		                "pd" : self.kg_to_pd(value),
		                "st_lb" : self.kg_to_st_lb(value),
		                "km" : self.m_to_km(value),
		                "mi" : self.m_to_mi(value),
		                "yd" : self.m_to_yd(value),
		}
		return conversions[target_unit]

	def temp_to_F(self, temp):
		tF = temp * 1.8 + 32
		return tF

	def temp_to_K(self, temp):
		tK = 273.15 + temp
		return tK

	def ms_to_kmh(self, speed):
		s_kmh = speed * 3.6
		return s_kmh

	def ms_to_mph(self, speed):
		s_mph = speed * 2.23694
		return s_mph

	def kg_to_pd(self, mass):
		m_pd = mass / 0.45359237
		return m_pd

	def kg_to_st_lb(self, mass):
		m_st = int(mass * 0.15747)
		m_lb = (mass - (m_st / 0.15747)) * 2.2046
		return (m_st, m_lb)

	def m_to_km(self, dist):
		d_km = dist / 1000
		return d_km

	def m_to_mi(self, dist):
		d_mi = dist / 1609.344
		return d_mi

	def m_to_yd(self, dist):
		d_yd = dist / 0.9144
		return d_yd

if __name__ == '__main__':
	u = units()

	tC = 20 #C
	print "C {} F {} K {}".format(tC, u.convert(tC, "F"), u.convert(tC, "K"))

	dist = 1854.3
	print "m {} km {} mi {} yd {}".format(dist, u.convert(dist, "km"),  
	u.convert(dist, "mi"), u.convert(dist, "yd"))

	mass = 79.5
	print "kg {} pd {} st/lb {}".format(mass, u.convert(mass, "pd"),  
	u.convert(mass ,"st_lb"))

	speed = 10
	print "m/s {} km/h {} mph {}".format(speed, u.convert(speed, "kmh"),  
	u.convert(speed, "mph"))


