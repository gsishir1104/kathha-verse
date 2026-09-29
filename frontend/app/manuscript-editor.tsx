'use client';
import {useEffect} from 'react';
import {useEditor,EditorContent} from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
const documentFor=(text:string)=>({type:'doc',content:text.split('\n\n').map(p=>({type:'paragraph',content:p?[{type:'text',text:p}]:[]}))});
export default function ManuscriptEditor({value,onChange,disabled}:{value:string;onChange:(v:string)=>void;disabled:boolean}){
 const editor=useEditor({immediatelyRender:false,extensions:[StarterKit.configure({bold:false,italic:false,strike:false,code:false,codeBlock:false,heading:false,blockquote:false,bulletList:false,orderedList:false,horizontalRule:false,link:false,underline:false})],content:documentFor(value),editorProps:{attributes:{'aria-label':'Chapter manuscript',role:'textbox','aria-multiline':'true',class:'tiptap-manuscript'}},onUpdate:({editor})=>onChange(editor.getText({blockSeparator:'\n\n'}))});
 useEffect(()=>{editor?.setEditable(!disabled)},[disabled,editor]);
 useEffect(()=>{if(editor&&editor.getText({blockSeparator:'\n\n'})!==value)editor.commands.setContent(documentFor(value),{emitUpdate:false})},[value,editor]);
 return <div><div className="studio-switch"><button type="button" className="button small" disabled={disabled||!editor} onClick={()=>editor?.chain().focus().undo().run()}>Undo</button><button type="button" className="button small" disabled={disabled||!editor} onClick={()=>editor?.chain().focus().redo().run()}>Redo</button><small>Manuscript text · autosaved after you pause</small></div><EditorContent editor={editor}/></div>
}
