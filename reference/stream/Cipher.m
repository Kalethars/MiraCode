f=fopen('carry.txt','r');
carry=fread(f);
fclose(f);
f=fopen('info.txt','r');
info=fread(f);
fclose(f);
count=0;
len=14;
for i=1:160
    s2=info((i-1)*8+1:i*8);
    s1=carry((i-1)*8*len+1:i*8*len);
    sum=s1(1:8);
    for j=2:len
        tmp=s1((j-1)*8+1:j*8);
        for k=1:8
            if sum(k)==tmp(k)
                sum(k)='0';
            else
                sum(k)='1';
            end
        end
    end
    flag=zeros(len);
    for j=1:8
        if sum(j)~=s2(j)
            r=random('unid',len);
            while flag(r)~=0
                r=random('unid',len);
            end
            flag(r)=1;
            if s1((r-1)*8+j)=='0'
                s1((r-1)*8+j)='1';
            else
                s1((r-1)*8+j)='0';
            end
            count=count+1;
        end
    end
    carry((i-1)*8*len+1:i*8*len)=s1;
end
f=fopen('ercipher.txt','w');
fprintf(f,'%s',carry);
fclose(f);
disp([num2str(count/4720*100),'%']);