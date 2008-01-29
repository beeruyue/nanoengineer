# Copyright 2007-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
DnaGroup.py - ... 

@author: Bruce
@version: $Id$
@copyright: 2007-2008 Nanorex, Inc.  See LICENSE file for details.
"""

from dna_model.Block import Block
from chunk           import Chunk

from constants import gensym

from icon_utilities import imagename_to_pixmap

from dna_updater.dna_updater_globals import _f_DnaGroup_for_homeless_objects_in_Part

from dna_updater.dna_updater_constants import DEBUG_DNA_UPDATER


# Following import is disabled. See addSegment method for reason.
## from dna_model.DnaSegment import DnaSegment

class DnaGroup(Block):
    """
    Model object which packages together some Dna Segments, Dna Strands,
    and other objects needed to represent all their PAM atoms and markers.

    The contents are not directly visible to the user in the model tree,
    except for Blocks (fyi, this behavior comes from our Block superclass,
    which is a kind of Group).
    
    But internally, most of the contents are Nodes which can be stored
    in mmp files, copied, and undo-scanned in the usual ways.

    Specific kinds of Group member contents include:
    - DnaStrands (optionally inside Blocks)
    - DnaSegments (ditto)
    - Blocks (a kind of Group)
    - DnaMarkers (a kind of Jig, probably always inside an owning
      DnaStrand or DnaSegment)
    - specialized chunks for holding PAM atoms:
      - DnaAxisChunk (undecided whether these will live inside DnaSegments
        they belong to, but probably they will)
      - DnaStrandChunk (undecided whether these will live inside their
        DnaStrands, but probably they will)

    As other attributes:
    - whatever other properties the user needs to assign, which are not
      covered by the member nodes or superclass attributes.
    """
    
    # The iconPath specifies path(string) of an icon that represents the 
    # objects of this class  
    iconPath = "modeltree/DNA.png"    
    hide_iconPath = "modeltree/DNA-hide.png"

    # This should be a tuple of classifications that appear in
    # files_mmp._GROUP_CLASSIFICATIONS, most general first.
    # See comment in class Group for more info. [bruce 080115]
    _mmp_group_classifications = ('DnaGroup',)
    
    # Open/closed state of the Dna Group in the Model Tree --
    # default closed. Note: this is ignored by the Model Tree code
    # (since we inherit from Block), but whether it affects any other code
    # (e.g. a PM display widget) is not yet decided.
    open = False
    
    def node_icon(self, display_prefs):
        """
        Model Tree node icon for the dna group node
        @see: Group.isHidden() 
        """
        del display_prefs # unused
        
        if self.isHidden():    
             return imagename_to_pixmap( self.hide_iconPath)
        else:
            return imagename_to_pixmap( self.iconPath)     

    def make_DnaStrandOrSegment_for_marker(self, controlling_marker, wholechain):
        """
        The given DnaMarker is either newly made to control wholechain,
        or old but newly controlling it; but it has no DnaStrandOrSegment.
        
        Make and return a new DnaStrand or DnaSegment
        (ask wholechain or marker what class to use)
        inside self (review: inside some Block?),
        perhaps making use of info in controlling_marker
        to help decide how to initialize some of its attributes.
        
        (Assume calling code will later move all chunks
        and markers from wholechain into the new object,
        and will store references to it as needed
        into controlling_marker and/or wholechain,
        so don't do those things here.)
        """
        class1 = controlling_marker.DnaStrandOrSegment_class()
        name = gensym(class1.__name__.split('.')[-1]) ###STUB -- should use class constant prefix, ensure unique names
            # todo: sensible name? (if we split a seg, is name related to old seg; if so how?)
        assy = controlling_marker.assy # it's a Jig so it has one
        obj = class1(name, assy, None) # note: these args are for Group.__init__
        self.addchild(obj)
        return obj
    
    # Note: some methods below this point are examples or experiments or stubs,
    # and are likely to be revised significantly or replaced.
    # [bruce 080115 comment]
    
    # example method:
    def get_segments(self):
        """
        Return a list of all our DnaSegment objects.
        """
        return self.get_topmost_subnodes_of_class('DnaSegment')
            # note: as of 080115 get_topmost_subnodes_of_class is implemented
            # for class args, but only for a few string args (including 'DnaSegment'),
            # and is untested. String args are useful for avoiding import cycles.

    def addSegment(self, segment):
        """
        Adds a new segment object for this dnaGroup.
        
        @param segment: The DnaSegment to be added to this DnaGroup object
        @type: B{DnaSegment}  
        """
        # importing DnaSegment created an import cycle which throws error. 
        # So this isinstance check is disabled for now.
        ## assert isinstance(segment, DnaSegment)
        
        self.addchild(segment)

    def getProps(self):
        """
	Method to support Dna duplex editing. see Group.__init__ for 
	a comment
        
        THIS IS THE DEFAULT IMPLEMENTATION. TO BE MODIFIED
	"""
        #Should it supply the Dna Segment list (children) and then add 
        #individual segments when setProps is called??
        # [probably not; see B&N email discussion from when this comment was added]
        if self.editCommand:
            props = ()
            return props

    def setProps(self, props):
        """
	Method  to support Dna duplex editing. see Group.__init__ for 
	a comment
        THIS IS THE DEFAULT IMPLEMENTATION. TO BE MODIFIED
	"""
        #Should it accept the Dna Segment list and then add individual segments?
        pass
    
    def edit(self):
        """
        @see: Group.edit()
        """
        commandSequencer = self.assy.w.commandSequencer
        commandSequencer.userEnterCommand('BUILD_DNA')
        currentCommand = commandSequencer.currentCommand
        assert currentCommand.commandName == 'BUILD_DNA'
        currentCommand.editStructure(self)
    
    def getStrands(self):
        """
        Returns a list of strands inside a DnaGroup object
        
        @return: A list containing all the strand objects
                 within self.
        @rtype: list
        
        @see: B{BuildDna_PropertyManager.updateStrandListWidget()} 
        @see: B{BuildDna_PropertyManager._currentSelectionParams}
        """
        #TO BE REVISED. As of 2008-01-17, it uses isinstance check for  
        #Chunk and some additional things to find out a list of strands inside
        # a DnaGroup -- Ninad 2008-01-17        
        strandList = []
        def filterSelectedStrands(node):
            if isinstance(node, Chunk) and node.isStrandChunk():
                strandList.append(node)    
                
        self.apply2all(filterSelectedStrands)
        
        return strandList
    
    def getSelectedStrands(self):
        """
        Returns a list of selected strands of the DnaGroup        
        @return: A list containing the selected strand objects
                 within self.
        @rtype: list
        """
        selectedStrandList = []
        for strand in self.getStrands():
            if strand.picked:
                selectedStrandList.append(strand)
        
        return selectedStrandList
    
    def getSelectedSegments(self):
        """
        Returns a list of segments whose all members are selected.        
        @return: A list containing the selected strand objects
                 within self.
        @rtype: list
        """
        #TODO: This is a TEMPORARY KLUDGE  until Dna model is fully functional. 
        #Must be revised. Basically it returns a list of DnaSegments whose 
        #all members are selected. 
        #See BuildDna_PropertyManager._currentSelectionParams() where it is used
        #-- Ninad 2008-01-18
        segmentList = self.get_segments()
        
        selectedSegmentList = []    
                                    
        for segment in segmentList:
            
            pickedNodes = []
            unpickedNodes = []
            
            def func(node):
                if isinstance(node, Chunk):
                    if not node.picked:
                        unpickedNodes.append(node)
                    else:
                        pickedNodes.append(node)   
                        
            segment.apply2all(func)
            
            if len(unpickedNodes) == 0 and pickedNodes:
                selectedSegmentList.append(segment)  
                
        return selectedSegmentList
 
    pass # end of class DnaGroup

# ==

def find_or_make_DnaGroup_for_homeless_object(node):
    """
    All DNA objects found outside of a DnaGroup during one run of the dna updater
    in one Part should be put into one new DnaGroup at the end of that Part.
    This is a fallback, since it only happens if we didn't sanitize DnaGroups
    when reading a file, or due to bugs in Dna-related user ops,
    or a user running an ordinary op on DNA that our UI is supposed to disallow.
    So don't worry much about prettiness, just correctness,
    though don't gratuitously discard info.

    The hard part is "during one run of the dna updater". We'll let it make a
    global dict from Part to this DnaGroup, and discard it after every run
    (so no need for this dict to be weak-keyed).

    If we have to guess the Part, we'll use the node's assy's current Part.
    """
    part = node.part or node.assy.part
    try:
        return _f_DnaGroup_for_homeless_objects_in_Part[part]
    except KeyError:
        dnaGroup = _make_DnaGroup_for_homeless_objects_in_Part(part)
        _f_DnaGroup_for_homeless_objects_in_Part[part] = dnaGroup
        return dnaGroup
    pass

def _make_DnaGroup_for_homeless_objects_in_Part(part):
    # not needed, done in addnode: part.ensure_toplevel_group()
    name = gensym("fallback DnaGroup")
    assy = part.assy #k
    dad = None
    dnaGroup = DnaGroup(name, assy, dad) # same args as for Group.__init__
    part.addnode(dnaGroup)
    if DEBUG_DNA_UPDATER:
        print "dna_updater fallback (bug, or mmp file not fixed when read): " \
              " made new dnaGroup %r" % dnaGroup
    return dnaGroup
    
# end
