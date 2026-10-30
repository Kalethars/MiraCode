print('[',end='')
refcount=0
refnow=0
p1=8
p2=11
for i in range(6):
    if i<5:
        print(refnow+1,end=' ')
    else:
        print(refnow+1)
    if refcount==0:
        refnow=(refnow+p1)%16
        refcount=1
    else:
        refnow=(refnow+p2)%16
        refcount=0
for i in range(10):
    if i<9:
        print(refnow+1,end=' ')
    else:
        print(refnow+1)
    if refcount==0:
        refnow=(refnow+p1)%16
        refcount=1
    else:
        refnow=(refnow+p2)%16
        refcount=0
for i in range(6):
    if i<5:
        print(refnow+1,end=' ')
    else:
        print(refnow+1)
    if refcount==0:
        refnow=(refnow+p1)%16
        refcount=1
    else:
        refnow=(refnow+p2)%16
        refcount=0
for i in range(10):
    if i<9:
        print(refnow+1,end=' ')
    else:
        print(refnow+1,end='];')
    if refcount==0:
        refnow=(refnow+p1)%16
        refcount=1
    else:
        refnow=(refnow+p2)%16
        refcount=0
