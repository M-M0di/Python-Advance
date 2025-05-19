# ADVANCED ***************************************************************************
# content = assignment
#
# date    = 2022-01-07
# email   = contact@alexanderrichtertd.com
#************************************************************************************

"""
CUBE CLASS

1. CREATE an abstract class "Cube" with the functions:
   translate(x, y, z), rotate(x, y, z), scale(x, y, z) and color(R, G, B)
   All functions store and print out the data in the cube (translate, rotate, scale and color).

2. ADD an __init__(name) and create 3 cube objects.

3. ADD the function print_status() which prints all the variables nicely formatted.

4. ADD the function update_transform(ttype, value).
   "ttype" can be "translate", "rotate" and "scale" while "value" is a list of 3 floats.
   This function should trigger either the translate, rotate or scale function.

   BONUS: Can you do it without using ifs?

5. CREATE a parent class "Object" which has a name, translate, rotate and scale.
   Use Object as the parent for your Cube class.
   Update the Cube class to not repeat the content of Object.

"""

class Cube:
   def __init__(self, name):
      self.name      = name
      self.translate = [0.0, 0.0, 0.0]
      self.rotate    = [0.0, 0.0, 0.0]
      self.scale     = [1.0, 1.0, 1.0]
      self.color     = [1.0, 1.0, 1.0]

   def print_status(self):
      print(f"""\
            Object Name : {self.name}
            Translate   : {self.translate}
            Rotation    : {self.rotate}
            Scale       : {self.scale}
            Color       : {self.color}""")
      
   def transform(self, ttype, value):
      transform_map = {
         "translate" : self.translate,
         "rotate"    : self.rotate,
         "scale"     : self.scale
      }

      for ttype in transform_map:
         transform_map[ttype] = value
         setattr(self, ttype, value)

cls_inst = Cube("Cube1")
cls_inst.print_status()
cls_inst.transform("translate", [1.0, 2.0, 3.0])
cls_inst.print_status()

print(cls_inst)



      

         