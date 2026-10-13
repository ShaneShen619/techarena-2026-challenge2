const ts=require('/Applications/Cursor.app/Contents/Resources/app/extensions/node_modules/typescript/lib/typescript.js');
const file='/Users/shane/.cursor/projects/Users-shane-Desktop-Arena-2/canvases/phase2-multistage-features.canvas.tsx';
const root='/Users/shane/.cursor/projects/Users-shane-Desktop-techarena-2026-topic1-template/canvases/node_modules/@types/react';
const config=ts.parseJsonConfigFileContent({files:[file],compilerOptions:{target:'ES2022',module:'ESNext',moduleResolution:'Bundler',jsx:'react-jsx',strict:true,skipLibCheck:true,noEmit:true,ignoreDeprecations:'6.0',baseUrl:'/',paths:{'cursor/canvas':['/Users/shane/.cursor/skills-cursor/canvas/sdk/index.d.ts'],'react':[root+'/index.d.ts'],'react/jsx-runtime':[root+'/jsx-runtime.d.ts']}}},ts.sys,'/');
const program=ts.createProgram(config.fileNames,config.options);const diagnostics=ts.getPreEmitDiagnostics(program);
console.log(ts.formatDiagnosticsWithColorAndContext(diagnostics,{getCurrentDirectory:()=>'/','getCanonicalFileName':f=>f,getNewLine:()=> '\n'}));console.log('Canvas TypeScript check:',diagnostics.length===0?'no errors':diagnostics.length+' errors');process.exitCode=diagnostics.length?1:0;
