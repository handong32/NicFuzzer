#include <stdio.h>
#include <stdlib.h>

union IxgbeLogEntry {
  long long data[12];
  struct {
    long long tsc;    
    long long ninstructions;
    long long ncycles;
    long long nref_cycles;
    long long nllc_miss;
    long long joules;
    long long c3;
    long long c6;
    long long c7;
        
    int rx_desc;
    int rx_bytes;
    int tx_desc;
    int tx_bytes;
    
    long long pad;
  } __attribute((packed)) Fields;
} __attribute((packed));

int main() {
  /* declare a file pointer */
  FILE    *infile;
  char    *buffer;
  long    numbytes;
  union IxgbeLogEntry *le;
  int i, num_entries;
  
  /* open an existing file for reading */
  infile = fopen("nc0.out", "r");
 
  /* quit if the file does not exist */
  if(infile == NULL)
    return 1;
 
  /* Get the number of bytes */
  fseek(infile, 0L, SEEK_END);
  numbytes = ftell(infile);
  num_entries = numbytes/sizeof(union IxgbeLogEntry);
  printf("numbytes=%lu num_entries=%d\n", numbytes, num_entries);
  
  /* reset the file position indicator to 
     the beginning of the file */
  fseek(infile, 0L, SEEK_SET);	
 
  /* grab sufficient memory for the 
     buffer to hold the text */
  buffer = (char*)calloc(numbytes, sizeof(char));	
 
  /* memory error */
  if(buffer == NULL) {
    printf("buffer == NULL\n");
    return 1;
  }
 
  /* copy all the text into the buffer */
  fread(buffer, sizeof(char), numbytes, infile);
  fclose(infile);
  
  le = (union IxgbeLogEntry *)buffer;
  for(i=0;i<10;i++) {
    printf("%d %d %d %d %d %llu %llu %llu %llu %llu %llu %llu %llu %llu\n",
	   i,
	   le[i].Fields.rx_desc, le[i].Fields.rx_bytes,
	   le[i].Fields.tx_desc, le[i].Fields.tx_bytes,
	   le[i].Fields.ninstructions,
	   le[i].Fields.ncycles,
	   le[i].Fields.nref_cycles,	     
	   le[i].Fields.nllc_miss,
	   le[i].Fields.c3,
	   le[i].Fields.c6,
	   le[i].Fields.c7,
	   le[i].Fields.joules,
	   le[i].Fields.tsc);
  }
  printf("******\n");
  for(i=num_entries-10;i<num_entries;i++) {
    printf("%d %d %d %d %d %llu %llu %llu %llu %llu %llu %llu %llu %llu\n",
	   i,
	   le[i].Fields.rx_desc, le[i].Fields.rx_bytes,
	   le[i].Fields.tx_desc, le[i].Fields.tx_bytes,
	   le[i].Fields.ninstructions,
	   le[i].Fields.ncycles,
	   le[i].Fields.nref_cycles,	     
	   le[i].Fields.nllc_miss,
	   le[i].Fields.c3,
	   le[i].Fields.c6,
	   le[i].Fields.c7,
	   le[i].Fields.joules,
	   le[i].Fields.tsc);
  }
  /* confirm we have read the file by
     outputing it to the console */
  //printf("The file called test.dat contains this text\n\n%s", buffer);
 
  /* free the memory we used for the buffer */
  //free(buffer);

}
