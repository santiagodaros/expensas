const fs = require("fs");
const path = "src/pages/Consorcios.tsx";
const TL = String.fromCharCode(96);
const DS = "$";

const content = [
"import { useState } from " + TL + "react" + TL + ";",
"import { useGet } from " + TL + "@/hooks/useApi" + TL + ";",
"import { Consorcio, ConsorcioCreate, Unidad, UnidadCreate } from " + TL + "@/types/api" + TL + ";",
"import api from " + TL + "@/lib/api" + TL + ";",
"import { Skeleton } from " + TL + "@/components/ui/skeleton" + TL + ";",
"import { Button } from " + TL + "@/components/ui/button" + TL + ";",
"import { Input } from " + TL + "@/components/ui/input" + TL + ";",
"import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from " + TL + "@/components/ui/dialog" + TL + ";",
"import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from " + TL + "@/components/ui/table" + TL + ";",
"import { Building2, Plus, Pencil, Trash2, Users, ChevronRight, MapPin, Hash } from " + TL + "lucide-react" + TL + ";",
"",
].join("\n");

fs.writeFileSync(path, content, "utf8");
console.log("written", content.length);
