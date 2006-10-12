'''
NewInval.py [to be cannibalized, mainly just for displist code]

$Id$
'''

class NewInval:
    def __getattr__(self, attr):
        if attr.startswith('_'):
            raise AttributeError, attr
        # begin tracking?
        try:
            method = getattr(self, '_c_' + attr)
            # this might recompute the method!
            # now, the method might need to be passed some indices. how does that work? we need a dict like object, not this!
            res = method()

        except:
            pass

class InvalDict(UserDict):
    def __getitem__(self, key):
        try:
            return self.data[key]
        except:
            self.data[key] = res = self.computefunc(key)
            return res
        pass
    pass

# then set up these things, depend on other things like themselves

if 1:
    for i, kid in ikids:
        pi = prior(i) # prior is specific to the index-set, might even be an attr (dictlike) itself
        # or is it an attr of our idea of the kid, which points to our idea of prior kid, and also knows index?


class GLPaneProxy: #######@@@@@@@ WRONG and/or OBS
    compiling_displist = 0
    def __init__(self):
        self.displists_needing_recompile_asap = {}
    def recompile_displists_that_need_it(self):
        while self.displists_needing_recompile_asap:
            listname, object = self.displists_needing_recompile_asap.popitem()
            if not self._not_needing_recompile.has_key(listname):
                # what we do next can add items to that dict, right? hmm, can they be the ones we already popped??? ######@@@@@@
                self._not_needing_recompile[listname] = object # maybe we have to store a counter (saying when they were up to date)??
                ### make sure that if they are in here, we don't think we need to remake them, or maybe check when we pull them out
                object.recompile_our_displist()
        return
    def glNewList(self, listname, mode):
        ###e assert current? no, callers already had to know that to safely call original form, so we can be the same way
        assert not self.compiling_displist
        glNewList(listname, mode)
        self.compiling_displist = listname #e also store the control object?
        return
    def glEndList(self, listname = None):
        if listname:
            assert listname == self.compiling_displist
        glEndList() # no arg
        self.compiling_displist = 0
        return
    def glCallList(self, listname):
        ###e in future, could merge successive calls into one call of multiple lists
        assert not self.compiling_displist # redundant with OpenGL only if we have no bugs in maintaining it, so worth checking
        glCallList(listname)
        return
    pass

class ComputeRuleMixin: pass
    ### superclass to use _compute_ rules... not sure what usage tracking it does in general; does it ask main class what to do?

######@@@@@@ Q: do we separate the object to own a displist, below, and the one to represent various Drawables,
# like one for DisplistChunk and one for defining a displist-subroutine?
# Do these even differ?
# If we do, is the class below even a Drawable with a draw method? (I doubt it. I bet it's an internal displist-owner helper object.)

from state_utils import transclose

# singleton object - layer of displist proxies

def ensure_ready_to_call( dlist_owner_1 ):
    """[private helper function]
    dlist_owner_1 should be a DisplistOwner; we use private attrs and/or methods of that class,
    including _key, _ensure_self_updated(), _direct_sublists_dict.
       Make sure that dlist_owner_1's displist can be safely called right after we return,
    with all displists that will call (directly or indirectly) up to date (in their content).
    Note that, in general, we won't know which displists will be called by a given one
    until after we've updated its content (and compiled calls to those displists as part of its content).
       Assume we are only called when our GL context is current and we're not presently compiling a displist in it.
    """
    toscan = { dlist_owner_1._key : dlist_owner_1 }
    def collector( obj1, dict1):
        dlist_owner = obj1
        dlist_owner._ensure_self_updated() # if necessary, sets or updates dlist_owner._direct_sublists_dict
        dict1.update( dlist_owner._direct_sublists_dict )
    transclose(  toscan, collector )
    return

class DisplistChunkInstance( ComputeRuleMixin): ######@@@@@ RENAME to DisplistOwner or so (or proxy? no, tho sort of.)
    """Each object of this class owns one OpenGL display list (initially unallocated) in a specific OpenGL context,
    and keeps track of whether its contents (OpenGL commands, as actually stored in our GL context) might be invalid,
    and whether any of its kids' contents might be invalid.
    (By "kids" here, we mean any displists ours calls, directly or indirectly.)
       We also need to know how to regenerate our displist's contents on demand, tracking all displists it directly calls,
    as well as doing the usual usage-tracking of modifiable values on which the contents depends.
    We record these things separately so we can be invalidated in the necessary ways.
       A main public method ensures that our contents and our kids' contents are up to date.
    The algorithm is to transclose on the set of displists we call (including self.displist),
    and by calling a private method of this class on each one, to ensure updatedness of its contents
    and of its record of its direct kids, allowing us to tranclose on the direct kids.
       We also have a public method to call our displist in immediate mode, which must first use the prior method
    to ensure updatedness of all displists that that would call. (That means it has to use GL_COMPILE followed by glCallList,
    not GL_COMPILE_AND_EXECUTE, since in the latter case, it might encounter an unexpected call to a kid displist which is not
    up to date, and have no way to make it up to date, since OpenGL doesn't permit recursive compiling of displists.)
       We also have a method to compile a call to self.displist, which although callable by arbitrary commands' drawing code,
    is semi-private in that it's only legally called while some object of this class is compiling a displist, 
    and it assumes there is a global place in which to record that displist call for use by that object's tracking of called displists.
    # ==
       To fit with the "maybe-inval" scheme for avoiding recomputes that we were warned might be needed, but turn out not to be
    (as detected by a recompute rule noticing old and new values of all inputs are equal, or "equal enough" for how it uses them),
    we would need a way of asking self.thing.draw whether its output (i.e. the OpenGL commands it generates, usually reported only
    by side effect on a GL context -- note that its direct kidlist is a function of that output) would actually be different than
    the last time we called it for compiling into our display list.
       This is not yet implemented... it would probably require separation of "asking for drawing code", "diffing that" (via a proxy
    version-counter, or perhaps by direct graph comparison of the code's rep), and executing that in some GL context. ###k
       BTW [digr], I think the maybe-inval scheme in general is just to pass on a maybe-inval signal, and later to be asked
    whether inval is really needed, and to ask kids the same, perhaps diffing their values... the hard part is that different
    users of one value need different answers, e.g. if one user used it so long ago that it changed and changed back since then,
    though other users used it when it was changed. This is why we can't only ask the kid -- we can, but even if it recomputes,
    we have to diff to really know. I suspect this means that it's equivalent to an ordinary inval scheme, with each function
    also optimizing by memoizing the answer given certain inputs, namely the last ones it used. I'm not sure of all this. ###k
       Summary of public methods:
    - call our displist in immediate mode
    - call it while compiling another displist
    [both of those are called by glpane when it's asked to call a displist, or an array of them; it switches on its flag of whether
     it's currently compiling a displist; if it is, it knows the owning object, so it can *ask that object* to make the record.]
    MAYBE WRONG?, they are called by self.draw... ok?? no, prob not... ######@@@@@@
    - report our displist name (this is just the public attribute self.displist, which has a recompute rule)
    """
    # maybe semi-obs comments:
    
    # belongs to one gl-displist-context
    # has self.displist (glpane displist id in that context)
    # has arg, self.thing, can redraw it - it's an instance of a drawable
    # maintains formula: thing's draw-effects is an input to this guy's draw-effects
    #  so if thing's draw-effects change, and something wants "return" (do, where specified) of self draw-effects,
    #  and that caller might or might not be itself making a displaylist,
    #  then we can do that (by emitting a call of this guy's displist, perhaps merged with other calls if we call several in a row)
    #  (that merging can be autodone by our glpane, if it records all gl commands -- hmm, that's errorprone, leave it for later,
    #   it doesn't affect this guy's code anyway)
    #  but for callers making a displist, only if we warn caller that before it runs that displist, it better have us recompile ours,
    #  which we do by adding ourself to a set in the calling env;
    #  whereas for callers not making a displist, only if we *first* remake ours, before emitting the call,
    #  *or* if we remake ours in compile-execute mode (equiv since when it later means smth else, that doesn't matter anymore
    #  since current cmds not being saved) (and i'm not sure it's always possible to first remake ours, then call it)
    #  (though we can try and see -- it's a user pref which is mainly for debugging, might affect speed or gl-bugs)
    
    # if thing's draw effects don't change, and smth wants us to draw, in either case we just emit a call of the displist.

    # default values of instance variables
    _direct_sublists_dict = 3 # intentional error if this default value is taken seriously
    
    def __init__(self):
        self._key = id(self)
        
    def _compute_displist(self): # compute method for self.displist ###IMPLEM compute methods
        ###NOTE usage tracking should turn up nothing -- we use nothing
        "allocate a new display list name (a 32-bit int) in our GL context"
        self.glpane.makeCurrent() # not sure when this compute method might get called, so make sure our GL context is current
        self.displist = self.glpane.glGenLists(1) # allocate the display list name [#k does this do makeCurrent??]
        # make sure it's a nonzero int or long
        assert type(self.displist) in (type(1), type(1L)) and self.displist
        return

    def _ensure_self_updated(self):
        """[private]
        Ensure updatedness of our displist's contents
        and of our record of its direct kids (other displists it directly calls).
        """
        self._direct_sublists_dict = 3 # intentional error if this value is taken seriously
        assert 0, 'nim' #######@@@@@@@
        
    def call_in_immediate_mode(self):
        self.ensure_ready_for_immediate_mode_call() ### change to external helper func, since it works on many objs of this class? yes.
        # or class method? (nah)
        self.call_our_displist() #### RENAME to make private


    # == old, some obs or wrong
    def draw(self): ######@@@@@@ prob wrong name, see above; also, wrong code
        # need to make sure we have a list allocated -- this is implicit in grabbing its opengl listname from self.displist
        assert self.displist
        if 'self.thing draw effects changed': #####@@@@@ how to find out? not in usual way, that would draw it right now!
            ### or can we say, that would return a routine to draw it???
            ## also what need we do, to say that we've updated to use this info? will running thing.draw revalidate it?
            # not in all contexts, just this one! will it incr a counter, so we can look and see which draw effects are latest
            # and which ones we last grabbed? yes, i think so, esp since other inval objects need to "diff" results,
            # and the number would stand for the results, hash them as it were. maybe we need it too for some reason.
            #####@@@@
            if self.glpane.compiling_displist:
                self.call_our_displist()
                self.ensure_our_displist_gets_recompiled_asap()
                    # (asap means before drawing the one being compiled, eg before any immediate mode drawing)
            else:
                # immediate mode - don't call it until it's remade!
                ###E also need to recompile any lists listed in self.glpane.displists_needing_recompile_asap!!! i thnk..
                if 'oneway':
                    self.recompile_our_displist()
                    self.glpane.recompile_displists_that_need_it() # might do more lists than before prior statement added some ###
                    self.call_our_displist()
                else: # anotherway -- is this possible? only if we know in advance which lists will get used by the following!
                    assert 0, "nim, since we need to know more..."
                    #e recompile_displists_that_need_it, including ones we're about to call in following statement
                    self.recompile_and_execute_our_displist()
                pass
            pass
        else:
            self.call_our_displist()
        return
    def recompile_and_execute_our_displist(self): ### who does usage tracking, general and displist?
        assert 0, "never called"
        self.glpane.glNewList(self.displist, GL_COMPILE_AND_EXECUTE)
            # note: not normally a glpane method, but we'll turn all gl calls into methods so that self.glpane can intercept
            # the ones it wants to (e.g. in this case, so it can update self.glpane.compiling_displist)
        self.thing.draw()
        self.glpane.glEndList(self.displist) # doesn't normally have an arg, but this lets glpane interception do more error-checking
        return
    def recompile_our_displist(self):
        self.glpane.glNewList(self.displist, GL_COMPILE)
        self.thing.draw()
        self.glpane.glEndList(self.displist)
        return
    def call_our_displist(self): ### immd mode or not? what do we vs caller do?
        self.glpane.glCallList(self.displist)
        return
    def ensure_our_displist_gets_recompiled_asap(self):
        self.glpane.displists_needing_recompile_asap[self.displist] = self
        return
    pass

# ==


class StandardInvalidatable: # scratch
    "One invalidatable value of the most standard kind."
    def inval(self):
        self.valid = 0
    def get_value(self):
        if not self.valid:
            self._recompute()
        return self._value
    def set_formula(self, formula):
        self.formula = formula
        self.inval()
    def _recompute(self):
        "[private; only call this when not valid]"
        #e do layer-prep things, like propogating inval signals from changedicts
        #e set up usage track
        # recompute (protect from exceptions?)
        newval = self.formula(self) # ??? have formula also report usage? who decides where to memo? is it a formula inst (owned)?
            # to decide -- what kinds of formulas can be ortho to kinds of invalidatable lvalues?
        #e end usage track
        #e diff old & new?
        #e send up-signals?
        self._value = newval
        return
    pass

class DisplistInvalidatable:
    pass ###
# several levels: opengl; invalidating a rewritable external subroutine; inval per se

# ==

# Tue 060919

# env + expr -> understood expr (in that env), an obj with attrs (oresmic?)
# expr + env/place -> placed expr;
#   done by a recompute rule, so it might get invalidated, and it's an attrval which is itself usage tracked
# env is divided up - for us, expr interp rules, state (model, transient, optim, displists), glpane & its state and coords
#   and we might yet have to declare or divide it based on what changes rarely, per drawable instance, or per frame (affects inval code)

# write these funcs so that their api does not preclude them from memoizing, or force them to

# they can be env methods, since env determines how they all work and holds the memos

# subenv for every expr level as i interpret, if necessary, or is it just a sub-place?
# but it might only exist during interp -- it's parallel to, but perhaps more transient than, yet more general than,
# transient-state container-hierarchy

# do that code walkthough for a simple example - simple MT with displists (on paper)

# then sort that code into methods on objects, then classes, then write it down in this style.

# overall - recompute rule in drawing env, from expr to its implem (where to send draw events)
# uses understood expr, which tells flags about whether it uses transient state, class or constructorfunc for creating drawable...

# expr object - return the head, and arglist incl options or that there is none, and lexical class from parser if any

# expr in env - understand it, incl how to make it, then make it (in place) (I guess place != env, env is that part of place
#    which affects understanding of expr, maybe not including the part that has changing vars at runtime, or even changing opt vals)
#    (but the understanding might say "opt X has type T" and then that might be what decided the val was in the other place,
#     for env opt vals? not sure.)

# ... maybe just write down the pseudocode for calling a display list in imm mode, which remakes some, which calls some in compiled mode?

# ==

class _Lval: ####@@@@ compare to later version in scratch5.py
    "I own a resettable formula (like a recompute callable, but usage-tracks), and maintain a lazy invalidatable .value."
    _invalid = True ### ok? what about propogation?
    _memoized_value = None
    _version_counter = 1 ###k ??
    
    def __init__(self):
        pass
    def invalidate(self):
        if not self._invalid:
            self._invalid = True
            ### also propogate?? yes, we have subscribers to inval... grab code from env.prefs system, changes.py i think #####@@@@@
    def __getattr__(self, attr):
        if attr == 'value':
            return self.get_value() ### use a property
        raise AttributeError, attr
    def get_value(self, args_each_time = None): # args_each_time can only be passed if you call this method explicitly
        "called whether or not we have the value"
        if self._invalid:
            self._recompute(args_each_time)
        return self._memoized_value
    def _recompute(self, args_each_time):
        "only called when we're invalid"
        new = self._compute_a_new_value(args_each_time)
        if new != self._memoized_value: # != ok? not for all numeric arrays? or is it? I forget. state_utils should say.
            self._version_counter += 1 ###k ??
            self._memoized_value = new
        self._invalid = False
        return
    def _compute_a_new_value(self, args_each_time):
        "return a newly computed value" ### what about usage tracking??
        return self._func(args_each_time)
            ###k actually call a formula, and let it usage-track for us, and we'll subscribe our inval to what we used.
            ### but does caller or this method do that? caller, since it might do funny things like choose memo place based on usage.    
    pass

class KidLval(_Lval):
    # this might have its own way to compute, ie a built-in python-coded formula-func, tho it might let superclass do usage tracking.
    # does that mean its own kind of formula, or an implicit builtin formula (since formulas do usage tracking)?
    def _raw_recompute(self, args_each_time): #####@@@@@ call me
        parent, index = args_each_time
        # this is where we put the code to ask the parent how to make that kid, and to make it,
        # but also, perhaps, to compare the inputs to last time and decide whether we really need to remake it (not sure).
        codeformula = parent._get_kid_codeformula(index) ####IMPLEM - this can change at runtime for the same kid, i think -- always remake then
        lexenv = parent._get_kid_lexenv(index) ####IMPLEM -- lexenv is an immutable and unchanging object, it's what we want here
        ###E compare codeformula to old value -- stored where??
        ## worse -- is it really a formula? how do we monitor changes? when do they mean we need a new kid? usually it's just 'code expr'...
        # lets assume that's what it is, for now.
        if 'need to recompute':
            'make a kid from lexenv, with index & code'
            code = codeformula
            kid = make_an_instance(code, lexenv, place)
                ####@@@@ also place? or, do we not even store that, but use it only at runtime? that might be a de-optim, but gives good flexibility --
                # lets instance run in multiple copies -- OTOH only if entire index chain is the same, so maybe it's a silly idea.
                #### wait, put in the index, relative to the parent... is it in the lexenv? I think so. no, only in spirit, as optim we separate it.
            return kid
        return None ##k??
    pass

def make_an_instance(code, lexenv, place):
    "somebody decided a new instance needs to be made, in a certain place (incl index_chain, storage)... make it."
    nim(pseudocode)
    return code(lexenv, place) # pseudocode ###@@@

# why not just pass the place-related make args, and decide locally what they contain (index, stores, etc), so we can change that later?
# and also the place-related each-frame args?? or do we have none of those? the old reasoning says none: they're often stable,
# so when they change we want to notice explicitly, so we optim for when they're stable.
# if we tried to let one instance live in two places, the optim data would all differ so we'd defeat the purpose.
# ... so the place-related args are all in make, and we might as well just call them the place!

class HelperClass:
    def __init__(self):
        self._kid_codeformulas = {} # convenience dict, of exceptions to whatever general rule we might have for these (??)
        self._kid_lexenvfuncs = {} # ditto, but missing or None ones are ok and mean "identity" (maybe)
        #e maybe one for coords? only in scenegraph model, not needed if we have _move
        self._kid_lvals = {} # this might define which kids we actually have (not sure, if set of kids could shrink & change back in one step)
        
    def _define_kid(self, index, codeformula = None, lexenvfunc = None): ### in general, is it best to pass these, or have a func to compute them?
        ####@@@@ decide by considering fancier-indexed iterators like Cube or Table.
        ### future note/digr:
        ### with fancy indexed sets with incremental inval, we'd need to receive inval signals for their pieces (values at indices).
        ### I imagine we could receive inval signals, new values, or mod-functions, or mod-func plus result
        ### (all of which are various portions of an "arrow" from old to new value of the piece in question).
        "[private] incremental make (or ensure made) of a kid"
        # pseudocode:
        new = not self._kid_lvals.has_key(index) # but even if not new, we might need to remake it... does that depend on code being new?
            # if so, is it automatic, from a diffing lval for the code, that will inval the kid-instance? #####@@@@@
        if new:
            self._kid_lvals[index] = KidLval(self, index) #### i don't like passing self (re cycles) -- maybe it won't need to store it??
            # what it might need it for is recomputing kid properties... maybe we can pass it self each time it needs that??
            # when it needs it is when we ask for the kid-value. hmm. Ditto for index I suppose?
        if codeformula is not None: # otherwise we're not preventing a subclass method from computing this (??)
            self._kid_codeformulas[index] = codeformula
        if lexenvfunc is not None: #### hmm, identity None is ambiguous with don't-change-it None, WRONG but tolerable for now ####@@@@
            self._kid_lexenvfuncs[index] = lexenvfunc
        #e something to be sure it's really made, or will be on demand; the kid needs to know its index
        #e something to see if we redefined those inputs? no, just guess we probably did if we called this
        self._kid_lvals[index].invalidate()
        #e how do we undefine a kid?
        return
    def _get_kid(self, index):
        ###e process saved-up kid index creations, if we ever buffer index creations from fancy indexed-set inputs
        lval = self._kid_lvals[index] # error if this does not exist, since keys define legal kids
        kid = lval.get_value( (self, index) ) # get the value -- the formula is assume to need this tuple of args, each time it runs,
            # and since we pass them, we're responsible for tracking invals in them and invalidating the kid
            # (as opposed to usage tracking occuring) ####@@@@ how does usage tracking fit in?
        return kid
    def _get_kid_lexenv(self, index):
        ###E memoize this -- really we want a recompute rule, i think... can it ever change? I don't think so...
        #e take parent lexenv, with localvars added, and use index to modify the various staterefs...
        # but how exactly does index interact, with different staterefs?
        # ... work that out later, ie write simple code now, quick to write & later read/revise.
        # uses of index: find transient state,
        # perhaps in various layers of differing permanence (ie same index-chain in different objects),
        # with varying sharing (ie different index-chains could point to same place, in some layer-objs but not others),
        # and also use it to get back to current coords: (index, parent) -> get to parent coords, then tell parent to get to mine via index.
        
        # something like: dict(_index = index, _inherit = parent-env) # where parent index chain is visible in _inherit, I guess... not sure & kluge.
        #### BTW it's so common for the index to be the only changing thing in the lexenv, that we might pass it in parallel as an optim/clarification.
        # then we ought to build up the chain explicitly as (local-index, parent-chain), and leave room for interning it as a key int, i suppose.
        # digr: do we intern it separately in separate layers? we might need to if they are persistent! (or intern it only in the most persistent one?)
        
        return self._lexenv # stub, and besides, are we supposed to store it? i suppose we might as well... could always zap if we finalize self...
    pass


# ==

