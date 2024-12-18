/*function do_resize(textboxId) {
    var minRows=3; 
    var maxRows=10; 
    var txt=textboxId.value;
    var cols=textboxId.cols;

    var arraytxt=txt.split('\n');
    var rows=arraytxt.length; 

if(rows < minRows){
  rows = minRows;
}
    for (i=minRows;i<arraytxt.length;i++) 
    rows+=parseInt(arraytxt[i].length/cols);

    if (rows>maxRows) textboxId.rows=maxRows;
    else textboxId.rows=rows;
}
*/