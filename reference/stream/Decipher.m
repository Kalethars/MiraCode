f=fopen('ercipher.txt','r');
s=fread(f);
fclose(f);
len=14;
info=zeros(1,160);
for i=1:160
    sum=s((i-1)*8*len+1:(i-1)*8*len+8);
    for j=2:len
        tmp=s((i-1)*8*len+(j-1)*8+1:(i-1)*8*len+j*8);
        for k=1:8
            if sum(k)==tmp(k)
                sum(k)='0';
            else
                sum(k)='1';
            end
        end
    end
    info((i-1)*8+1:i*8)=sum;
end
f=fopen('decipher.txt','w');
fprintf(f,'%s',info);
fclose(f);