/* BG_EET_RU V138: bounded native attempt ledger, SOURCE / TEST ONLY.
 * NOT a DLL to load into Baldur.exe. No hook, no linker into game, no memory reads.
 * The eventual hook must independently prove Win64 callback ABI, item struct layout,
 * valid thread/frame provenance, SEH/unwind and direct-render token ownership.
 * CItem pointers are NEVER retained. Returned raw bytes are NEVER mapped to HIT/MISS.
 * All calls are non-blocking; concurrent contention fails CLOSED.
 */
#if defined(_WIN32)
#define BG_API __declspec(dllexport)
#else
#define BG_API __attribute__((visibility("default")))
#endif
typedef unsigned long long bg_u64;
typedef unsigned int bg_u32;
typedef unsigned short bg_u16;
typedef unsigned char bg_u8;
#define BG_THREADS 24
#define BG_DEPTH 16
#define BG_RECORDS 512
#define BG_MAX_JSON_ID 9007199254740991ULL
#define BG_OK 0
#define BG_INVALID (-1)
#define BG_BUSY (-2)
#define BG_OVERFLOW (-3)
#define BG_MISMATCH (-4)
#define BG_POISONED (-5)
#define BG_NOT_FOUND (-6)
#define BG_DUPLICATE (-7)

/* A single thread/frame/seq is a candidate only; no native/user proof flags. */
typedef struct { bg_u8 bytes[8]; bg_u8 length; } BG_Resref;
typedef struct {
 bg_u64 session, thread, frame, seq, attacker, target;
 bg_u16 ability;
 bg_u8 raw_return, raw_return_present, render_count, valid;
 bg_u64 row_token; /* Direct renderer must supply this, NEVER infer from text. */
 char weapon[9], launcher[9], ammo[9];
} BG_Event;
typedef struct {
 bg_u64 thread;
 bg_u16 depth;
 bg_u8 active;
 BG_Event stack[BG_DEPTH];
} BG_Thread;
typedef struct {
 volatile bg_u32 busy;
 bg_u64 session, next_seq, dropped;
 bg_u16 records_len;
 bg_u8 poisoned;
 BG_Thread threads[BG_THREADS];
 BG_Event completed[BG_RECORDS];
} BG_Ledger;
static BG_Ledger g;
static int lock_ledger(void){return __atomic_exchange_n(&g.busy,1,__ATOMIC_ACQUIRE)==0;}
static void unlock_ledger(void){__atomic_store_n(&g.busy,0,__ATOMIC_RELEASE);}
static void zero_bytes(void *p,bg_u64 n){bg_u8 *b=(bg_u8*)p;while(n--)*b++=0;}
/* Does not require a NUL terminator. Exactly length bytes in a fixed 8-byte
 * snapshot are read. A CResRef pointer/struct must NOT be passed directly. */
static int copy_resref(char out[9],const BG_Resref *src,int required){
 bg_u32 i;
 for(i=0;i<9;i++)out[i]=0;
 if(!src)return required?0:1;
 if(src->length>8 || (required && src->length==0))return 0;
 for(i=0;i<src->length;i++){
  unsigned char c=src->bytes[i];
  if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'))return 0;
  out[i]=(char)c;
 }
 return 1;
}

static BG_Thread *get_thread(bg_u64 thread,int create){
 bg_u32 i;
 BG_Thread *free_slot=0;
 for(i=0;i<BG_THREADS;i++){
  if(g.threads[i].active && g.threads[i].thread==thread)return &g.threads[i];
  if(!g.threads[i].active && !free_slot)free_slot=&g.threads[i];
 }
 if(!create || !free_slot)return 0;
 zero_bytes(free_slot,sizeof(*free_slot));
 free_slot->active=1;free_slot->thread=thread;
 return free_slot;
}
static void poison_thread(BG_Thread *t){
 if(t){g.dropped+=t->depth;zero_bytes(t,sizeof(*t));}
}
BG_API int bgv138_reset(bg_u64 session){
 if(!session)return BG_INVALID;
 if(!lock_ledger())return BG_BUSY;
 /* Reset cannot interleave with a live attempt: leave current state intact. */
 for(bg_u32 i=0;i<BG_THREADS;i++)if(g.threads[i].active){unlock_ledger();return BG_MISMATCH;}
 zero_bytes((bg_u8*)&g+sizeof(g.busy),sizeof(g)-sizeof(g.busy)); /* Leave the spin guard held; clear padding too. */
 g.session=session;
 unlock_ledger();return BG_OK;
}
BG_API int bgv138_enter(bg_u64 session,bg_u64 thread,bg_u64 frame,
 bg_u64 attacker,bg_u64 target,const BG_Resref *weapon,const BG_Resref *launcher,
 const BG_Resref *ammo,bg_u16 ability,bg_u64 *seq_out){
 if(!seq_out||!session||!thread||!frame||!attacker||!target)return BG_INVALID;
 *seq_out=0;
 if(!lock_ledger())return BG_BUSY;
 if(g.poisoned||g.session!=session){unlock_ledger();return BG_POISONED;}
 if(g.next_seq>=BG_MAX_JSON_ID||g.records_len>=BG_RECORDS){g.poisoned=1;unlock_ledger();return BG_OVERFLOW;}
 BG_Thread *t=get_thread(thread,1);
 if(!t){g.poisoned=1;unlock_ledger();return BG_OVERFLOW;}
 if(t->depth>=BG_DEPTH){poison_thread(t);g.poisoned=1;unlock_ledger();return BG_OVERFLOW;}
 for(bg_u32 i=0;i<t->depth;i++)if(t->stack[i].frame==frame){poison_thread(t);unlock_ledger();return BG_DUPLICATE;}
 BG_Event event;zero_bytes(&event,sizeof(event));
 if(!copy_resref(event.weapon,weapon,1)||
    !copy_resref(event.launcher,launcher,0)||
    !copy_resref(event.ammo,ammo,0)){
  unlock_ledger();return BG_INVALID;
 }
 event.session=session;event.thread=thread;event.frame=frame;
 event.seq=++g.next_seq;event.attacker=attacker;event.target=target;
 event.ability=ability;event.valid=1;
 t->stack[t->depth++]=event;
 *seq_out=event.seq;
 unlock_ledger();return BG_OK;
}
BG_API int bgv138_exit(bg_u64 session,bg_u64 thread,bg_u64 frame,
 bg_u64 seq,bg_u8 raw_return){
 if(!session||!thread||!frame||!seq)return BG_INVALID;
 if(!lock_ledger())return BG_BUSY;
 if(g.poisoned||g.session!=session){unlock_ledger();return BG_POISONED;}
 BG_Thread *t=get_thread(thread,0);
 if(!t || !t->depth){unlock_ledger();return BG_NOT_FOUND;}
 BG_Event *top=&t->stack[t->depth-1];
 if(top->seq!=seq||top->frame!=frame||top->session!=session){
  poison_thread(t);unlock_ledger();return BG_MISMATCH;
 }
 if(g.records_len>=BG_RECORDS){poison_thread(t);g.poisoned=1;unlock_ledger();return BG_OVERFLOW;}
 BG_Event done=*top;done.raw_return=raw_return;done.raw_return_present=1;
 g.completed[g.records_len++]=done;
 zero_bytes(top,sizeof(*top));
 t->depth--;
 if(t->depth==0)zero_bytes(t,sizeof(*t));
 unlock_ledger();return BG_OK;
}
/* Called ONLY by a future independently-proven renderer hook, not a text parser.
 * The token is supplied from the renderer; no automatic UI association occurs.
 * This source-only function does NOT assert the supplied token's provenance. */
BG_API int bgv138_direct_render(bg_u64 session,bg_u64 seq,bg_u64 row_token){
 if(!session||!seq||!row_token)return BG_INVALID;
 if(!lock_ledger())return BG_BUSY;
 if(g.poisoned||g.session!=session){unlock_ledger();return BG_POISONED;}
 BG_Event *target=0;
 for(bg_u32 i=0;i<g.records_len;i++){
  BG_Event *r=&g.completed[i];
  if(r->seq==seq&&r->session==session)target=r;
  if(r->row_token==row_token&&r->render_count){unlock_ledger();return BG_DUPLICATE;}
 }
 if(!target){unlock_ledger();return BG_NOT_FOUND;}
 if(target->render_count){unlock_ledger();return BG_DUPLICATE;}
 target->row_token=row_token;target->render_count=1;
 unlock_ledger();return BG_OK;
}
BG_API int bgv138_read(bg_u64 session,bg_u64 seq,BG_Event *out){
 if(!out||!session||!seq)return BG_INVALID;
 if(!lock_ledger())return BG_BUSY;
 if(g.poisoned||g.session!=session){unlock_ledger();return BG_POISONED;}
 for(bg_u32 i=0;i<g.records_len;i++){
  if(g.completed[i].session==session&&g.completed[i].seq==seq){
   *out=g.completed[i];unlock_ledger();return BG_OK;
  }
 }
 unlock_ledger();return BG_NOT_FOUND;
}
BG_API int bgv138_stats(bg_u64 session,bg_u64 *completed,bg_u64 *dropped,bg_u8 *poisoned){
 if(!completed||!dropped||!poisoned)return BG_INVALID;
 if(!lock_ledger())return BG_BUSY;
 if(g.session!=session){unlock_ledger();return BG_POISONED;}
 *completed=g.records_len;*dropped=g.dropped;*poisoned=g.poisoned;
 unlock_ledger();return BG_OK;
}
