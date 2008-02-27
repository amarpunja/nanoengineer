# Copyright 2007-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
DnaLadderRailChunk.py - 

@author: Bruce
@version: $Id$
@copyright: 2007-2008 Nanorex, Inc.  See LICENSE file for details.
"""

from chunk import Chunk

from constants import gensym
from constants import black
from constants import ave_colors

from dna_updater.dna_updater_constants import DEBUG_DNA_UPDATER

import env
from utilities.Log import orangemsg, graymsg

# see also:
## from dna_model.DnaLadder import _rail_end_atom_to_ladder
# (below, perhaps in a cycle)

# ==

_DEBUG_HIDDEN = True ### TEMPORARY, but True for commit for now; but soon, remove the code for this @@@@

_superclass = Chunk

class DnaLadderRailChunk(Chunk):
    """
    """

    # initial values of instance variables:
    
##    chain = None # will be a DnaChain in finished instances #k needed? probably... actually i am not sure why, let's find out @@@@
##        # only used in wholechain._make_new_controlling_marker; guess not needed... removed that use [080120 7pm untested]

    wholechain = None # will be a WholeChain once dna_updater is done (can be set to None by Undo ### REVIEW CODE FOR THAT @@@@) --
        # set by update_PAM_chunks in the updater run that made self,
        # and again in each updater run that made a new wholechain
        # running through self
    
    ladder = None # will be a DnaLadder in finished instances; can be set to None by Undo #### FIX MORE CODE FOR THAT @@@@

    _num_old_atoms_hidden = 0
    _num_old_atoms_not_hidden = 0
    
    ###e todo: undo, copy for those attrs?

    # == init methods

    def __init__(self, assy, chain_or_something_else):

        if _DEBUG_HIDDEN:
            self._atoms_were_hidden = []
            self._atoms_were_not_hidden = []
            self._num_extra_bondpoints = 0

        # TODO: check if this arg signature is ok re undo, copy, etc;
        # and if ok for rest of Node API if that matters for this kind of chunk;
        # for now just assume chain_or_something_else is a DnaChain
        chain = chain_or_something_else
        # name should not be seen, but it is for now...
        name = gensym(self.__class__.__name__.split('.')[-1]) + ' (internal)'
        _superclass.__init__(self, assy, name)
##        self.chain = chain
        # add atoms before setting self.ladder, so adding them doesn't invalidate it
        self._grab_atoms_from_chain(chain) #e we might change when this is done, if we implem copy for this class
        # following import is a KLUGE to avoid recursive import
        # (still has import cycle, ought to ### FIX -- should refile that func somehow)
        from dna_model.DnaLadder import _rail_end_atom_to_ladder
            # todo: make not private... or get by without it here (another init arg??)
            # review: make this import toplevel? right now it's probably in a cycle.
        self.ladder = _rail_end_atom_to_ladder( chain.baseatoms[0] )
        self._set_properties_from_grab_atom_info()

        return

    def _undo_update(self):
        # this implem is basically just a guess @@@
        if self.wholechain:
            self.wholechain.destroy() # IMPLEM
            self.wholechain = None
##        self.chain = None #k ok?
        self.invalidate_ladder() # review: sufficient? set it to None?
        _superclass._undo_update(self)
        return
    
    def _grab_atoms_from_chain(self, chain):
        """
        Assume we're empty of atoms;
        pull in all baseatoms from the given DnaChain,
        plus whatever bondpoints or Pl atoms are attached to them
        (but only Pl atoms which are not already in other DnaLadderRailChunks).
        """
        # common code -- just pull in baseatoms and their bondpoints.
        # subclass must extend as needed.
        for atom in chain.baseatoms:
            self._grab_atom(atom)
                # note: this immediately kills atom's old chunk if it becomes empty
        return

    def _grab_atom(self, atom):
        """
        Grab the given atom (and its bondpoints) to be one of our own,
        recording info about its old chunk which will be used later
        (in self._set_properties_from_grab_atom_info, called at end of __init__)
        in setting properties of self to imitate those of our atoms' old chunks.
        """
        # first grab info
        old_chunk = atom.molecule
        # maybe: self._old_chunks[id(old_chunk)] = old_chunk
        if old_chunk and old_chunk.hidden:
            self._num_old_atoms_hidden += 1
            if _DEBUG_HIDDEN:
                self._atoms_were_hidden.append( (atom, old_chunk) )
        else:
            self._num_old_atoms_not_hidden += 1
            if _DEBUG_HIDDEN:
                self._atoms_were_not_hidden.append( (atom, old_chunk) )
        
        # then grab the atom
        if _DEBUG_HIDDEN:
            have = len(self.atoms)
        atom.hopmol(self)
            # note: hopmol immediately kills old chunk if it becomes empty
        if _DEBUG_HIDDEN:
            extra = len(self.atoms) - (have + 1)
            self._num_extra_bondpoints += extra
        return

    def _set_properties_from_grab_atom_info(self): # 080201
        # if *all* atoms were hidden, hide self.
        # if any or all were hidden, emit an appropriate summary message.
        if self._num_old_atoms_hidden and not self._num_old_atoms_not_hidden:
            self.hide()
            if DEBUG_DNA_UPDATER:
                summary_format = "DNA updater: debug fyi: remade [N] hidden chunk(s)"
                env.history.deferred_summary_message( graymsg(summary_format) )
        elif self._num_old_atoms_hidden:
            summary_format = "Warning: DNA updater unhid [N] hidden atom(s)"
            env.history.deferred_summary_message( orangemsg(summary_format),
                                                  count = self._num_old_atoms_hidden
                                                 )
            if DEBUG_DNA_UPDATER:
                ## todo: summary_format2 = "Note: it unhid them due to [N] unhidden atom(s)"
                summary_format2 = "Note: DNA updater must unhide some hidden atoms due to [N] unhidden atom(s)"
                env.history.deferred_summary_message( graymsg(summary_format2),
                                                      ## todo: sort_after = summary_format, -- or orangemsg(summary_format)??
                                                      count = self._num_old_atoms_not_hidden
                                                     )
        if self._num_old_atoms_hidden + self._num_old_atoms_not_hidden > len(self.atoms):
            env.history.redmsg("Bug in DNA updater, see console prints")
            print "Bug in DNA updater: _num_old_atoms_hidden %r + self._num_old_atoms_not_hidden %r > len(self.atoms) %r, for %r" % \
                  ( self._num_old_atoms_hidden , self._num_old_atoms_not_hidden, len(self.atoms), self )

        if _DEBUG_HIDDEN:
            mixed = not not (self._atoms_were_hidden and self._atoms_were_not_hidden)
            if not len(self._atoms_were_hidden) + len(self._atoms_were_not_hidden) == len(self.atoms) - self._num_extra_bondpoints:
                print "\n***BUG: " \
                   "hidden %d, unhidden %d, sum %d, not equal to total %d - extrabps %d, in %r" % \
                   ( len(self._atoms_were_hidden) , len(self._atoms_were_not_hidden),
                     len(self._atoms_were_hidden) + len(self._atoms_were_not_hidden),
                     len(self.atoms),
                     self._num_extra_bondpoints,
                     self )
                missing_atoms = dict(self.atoms) # copy here, modify this copy below
                for atom, chunk in self._atoms_were_hidden + self._atoms_were_not_hidden:
                    del missing_atoms[atom.key] # always there? bad bug if not, i think!
                print "\n *** leftover atoms (including %d extra bonpoints): %r" % \
                      (self._num_extra_bondpoints, missing_atoms.values())
            else:
                if not ( mixed == (not not (self._num_old_atoms_hidden and self._num_old_atoms_not_hidden)) ):
                    print "\n*** BUG: mixed = %r but self._num_old_atoms_hidden = %d, len(self.atoms) = %d, in %r" % \
                          ( mixed, self._num_old_atoms_hidden , len(self.atoms), self)
            if mixed:
                print "\n_DEBUG_HIDDEN fyi: hidden atoms = %r \n unhidden atoms = %r" % \
                      ( self._atoms_were_hidden, self._atoms_were_not_hidden )
        return
        
    def set_wholechain(self, wholechain):
        """
        [to be called by dna updater]
        @param wholechain: a new WholeChain which owns us (not None)
        """
        assert wholechain
        # note: self.wholechain might or might not be None when this is called
        # (it's None for new chunks, but not for old ones now on new wholechains)
        self.wholechain = wholechain

    def forget_wholechain(self, wholechain):
        """
        Remove any references we have to wholechain.
        
        @param wholechain: a WholeChain which refs us and is being destroyed
        """
        assert wholechain
        if self.wholechain is wholechain:
            self.wholechain = None
        return
        
    # == invalidation-related methods
    
    def invalidate_ladder(self): #bruce 071203
        """
        [overrides Chunk method]
        [only legal after init, not during it, thus not in self.addatom --
         that might be obs as of 080120 since i now check for self.ladder... not sure]
        """
        if self.ladder: # cond added 080120
            self.ladder.invalidate()
        return

    def in_a_valid_ladder(self): #bruce 071203
        """
        Is this chunk a rail of a valid DnaLadder?
        [overrides Chunk method]
        """
        return self.ladder and self.ladder.valid

    # == override Chunk methods related to invalidation

    def addatom(self, atom):
        _superclass.addatom(self, atom)
        if self.ladder and self.ladder.valid:
            # this happens for bondpoints (presumably when they're added since
            # we broke a bond); I doubt it happens for anything else,
            # but let's find out (in a very safe way, tho a bit unclear):
            # (update, 080120: I think it would happen in self.merge(other)
            #  except that we're inlined there! So it might happen if an atom
            #  gets deposited on self, too. ### REVIEW)
            if atom.element.eltnum != 0:
                print "dna updater, fyi: %r.addatom %r invals %r" % (self, atom, self.ladder)
            self.ladder.invalidate()
        return

    def delatom(self, atom):
        _superclass.delatom(self, atom)
        if self.ladder and self.ladder.valid:
            self.ladder.invalidate()
        return

    def merge(self, other): # overridden just for debug, 080120 9pm
        if DEBUG_DNA_UPDATER:
            print "dna updater debug: fyi: calling %r.merge(%r)" % (self, other)
        return _superclass.merge(self, other)

    def invalidate_atom_lists(self):
        """
        override superclass method, to catch some inlinings of addatom/delatom:
        * in undo_archive
        * in chunk.merge
        * in chunk.copy_full_in_mapping (of the copy -- won't help unless we use self.__class__ to copy) ### REVIEW @@@@
        also catches addatom/delatom themselves (so above overrides are not needed??)
        """
        if self.ladder and self.ladder.valid:
            self.ladder.invalidate() # 080120 10pm bugfix
        return _superclass.invalidate_atom_lists(self)
        
    # == other methods
    
    def modify_color_for_error(self, color):
        """
        Given the drawing color for this chunk, or None if element colors
        should be used, either return it unchanged, or modify it to
        indicate an error or warning condition (if one exists on this chunk).
        """
        error = self.ladder and self.ladder.error
            # maybe: use self.ladder.drawing_color(), if not None??
        if error:
            # use black, or mix it into the selection color [bruce 080210]
            if self.picked and color is not None:
                # color is presumably the selection color
                color = ave_colors(0.75, black, color)
            else:
                color = black
        return color
    
    pass # end of class DnaLadderRailChunk

# == these subclasses might be moved to separate files, if they get long

class DnaAxisChunk(DnaLadderRailChunk):
    """
    Chunk for holding part of a Dna Segment Axis (the part in a single DnaLadder).

    Internal model object; same comments as in DnaStrandChunk docstring apply.
    """
    def isAxisChunk(self):
        """
        This should always return True. It directly returns True ... bypassing
        the things done in Chunk class ... thereby making this a little faster.
        @see: Chunk.isAxisChunk() , overridden here.  
        """
        return True
    
    def isStrandChunk(self):
        """
        This should always return False. It directly returns False ... bypassing
        the things done in Chunk class ... thereby making this a little faster.
        @see: Chunk.isStrandChunk() , overridden here.  
        """
        return not self.isAxisChunk()
    
    pass

# ==

class DnaStrandChunk(DnaLadderRailChunk):
    """
    Chunk for holding part of a Dna Strand (the part in a single DnaLadder).

    Internal model object -- won't be directly user-visible (for MT, selection, etc)
    when dna updater is complete. But it's a normal member of the internal model tree for
    purposes of copy, undo, mmp file, internal selection, draw.
    (Whether copy implem makes another chunk of this class, or relies on dna
    updater to make one, is not yet decided. Likewise, whether self.draw is
    normally called is not yet decided.)
    """
    def isAxisChunk(self):
        """
        This should always return False. It directly returns False ... bypassing
        the things done in Chunk class ... thereby making this a little faster. 
        
        @see: Chunk.isAxisChunk() overridden here.          
        @see: DnaAxisChunk.isAxisChunk()
        """
        return False
    
    def isStrandChunk(self):
        """
        This should always return True. It directly returns True ... bypassing
        the things done in Chunk class ... thereby making this a little faster. 
        @see: Chunk.isStrandChunk() , overridden here.         
        """
        return not self.isAxisChunk()
    
    def _grab_atoms_from_chain(self, chain): # misnamed, doesn't take them out of chain
        """
        [extends superclass version]
        """
        DnaLadderRailChunk._grab_atoms_from_chain(self, chain)
        for atom in chain.baseatoms:
            # pull in Pls too (if they prefer this Ss to their other one)
            # and also directly bonded unpaired base atoms (which should
            # never be bonded to more than one Ss)
            ### review: can't these atoms be in an older chunk of the same class
            # from a prior step?? I think yes... so always pull them in,
            # regardless of class of their current chunk.
            for atom2 in atom.neighbors():
                grab_atom2 = False # might be changed to True below
                is_Pl = atom2.element.symbol.startswith('Pl') # KLUGE
                if is_Pl:
                    # does it prefer to stick with atom (over its other Ss neighbors, if any)?
                    if atom is atom2.Pl_preferred_Ss_neighbor(): # an Ss or None
                        grab_atom2 = True
                elif atom2.element.role == 'unpaired-base':
                    grab_atom2 = True
                if grab_atom2:
                    if atom2.molecule is self:
                        print "dna updater: should not happen: %r is already in %r" % \
                              (atom2, self)
                        # since self is new, just now being made,
                        # and since we think only one Ss can want to pull in atom2
                    else:
                        ## atom2.hopmol(self)
                        self._grab_atom(atom2)
                            # review: does this harm the chunk losing it if it too is new? @@@
                            # (guess: yes; since we overrode delatom to panic... not sure about Pl etc)
                            # academic for now, since it can't be new, afaik
                            # (unless some unpaired-base atom is bonded to two Ss atoms,
                            #  which we ought to prevent in the earlier bond-checker @@@@ NIM)
                            # (or except for inconsistent bond directions, ditto)
                        pass
                    pass
                continue
            continue
        return # from _grab_atoms_from_chain
    pass # end of class DnaStrandChunk

# end
