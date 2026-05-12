import React from "react";
import {
  Home,
  Users,
  BookOpen,
  Bot,
  Code2,
  Megaphone,
  Calendar,
  KeyRound,
  ClipboardList,
  Landmark,
  FileText,
  UserCog,
  File,
  MessageSquare,
  CircleDollarSign,
  UserPlus,
  Plus,
  Circle,
  ChevronUp,
  ChevronDown,
  Clock,
  Download,
} from "lucide-react";
import atgLogoPng from "../../Images/Atg_Logo.png";

export const ATGLogo = () => (
  <img src={atgLogoPng} alt="ATG Logo" width="32" height="32" style={{ display: "block" }} />
);

export const IconHome = ({ active }) => (
  <Home size={20} color={active ? "#1D44B0" : "#60676D"} absoluteStrokeWidth />
);

export const IconHRMS = () => (
  <Users size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconLMS = () => (
  <BookOpen size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconMCP = () => (
  <Bot size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconDevProject = () => (
  <Code2 size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconMarketing = () => (
  <Megaphone size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconCalendar = () => (
  <Calendar size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconPassword = () => (
  <KeyRound size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconAssessments = () => (
  <ClipboardList size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconBank = () => (
  <Landmark size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconPayslip = () => (
  <FileText size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconManageEmployees = () => (
  <UserCog size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconDocument = () => (
  <File size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconFeedback = () => (
  <MessageSquare size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconFinance = () => (
  <CircleDollarSign size={18} color="#60676D" absoluteStrokeWidth />
);

export const IconNewEmployee = () => (
  <UserPlus size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconDelayManagement = () => (
  <Clock size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconPayrollDownload = () => (
  <Download size={20} color="#60676D" absoluteStrokeWidth />
);

export const IconAdd = () => (
  <Plus size={20} color="#60676D" />
);

export const IconDot = () => (
  <Circle size={16} fill="#1D44B0" color="#1D44B0" />
);

export const SvgChevronUp = () => (
  <ChevronUp size={20} color="#60676D" absoluteStrokeWidth />
);

export const SvgChevronDown = () => (
  <ChevronDown size={20} color="#60676D" absoluteStrokeWidth />
);

export const TaskListIcon = () => (
  <svg width="32" height="32" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M6.752.25H18V3.375H6.75V2.25ZM6.759V7.875H18V9H6.75ZM6.7514.625V13.5H18V14.625H6.75ZM2.256.75C2.560556.752.850596.808593.120126.92578C3.389657.042973.629887.20413.840827.40918C4.051767.614264.212897.851564.324228.12109C4.435558.390624.494148.683594.59C4.59.310554.441419.600594.324229.87012C4.2070310.13964.045910.37993.8408210.5908C3.6357410.80183.3984410.96293.1289111.0742C2.8593811.18552.5664111.24412.2511.25C1.9394511.251.6494111.19141.3798811.0742C1.1103510.9570.87011710.79590.6591810.5908C0.44824210.38570.28710910.14840.1757819.87891C0.06445319.609380.005859389.3164109C08.689450.05859388.399410.1757818.12988C0.2929697.860350.4541027.620120.659187.40918C0.8642587.198241.101567.037111.371096.92578C1.640626.814451.933596.755862.256.75Z" fill="#000"/>
  </svg>
);

export const AlarmIcon = () => (
  <svg width="32" height="32" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M9.582425C11.24512.82975.6584814.00186.83058C15.17398.0026915.83249.592415.832411.25C15.832412.907615.173914.497314.001815.6694C12.829716.841511.2417.59.5824217.5C7.9248217.56.3351116.84155.16315.6694C3.990914.49733.3324212.90763.3324211.25C3.332429.59243.99098.002695.1636.83058C6.335115.658487.9248259.582425ZM9.582425.83333C8.145835.833336.768086.404025.752267.41984C4.736448.435664.165769.813414.1657611.25C4.1657612.68664.7364414.06435.7522615.0802C6.7680816.0968.1458316.66679.5824216.6667C11.01916.666712.396816.09613.412615.0802C14.428414.064314.999112.686614.999111.25C14.99919.8134114.42848.4356613.41267.41984C12.39686.4040211.0195.833339.582425.83333ZM9.165767.5H9.99909V11.1333L12.540812.3167L12.190813.075L9.1657611.6667V7.5ZM12.70744.375L13.24083.75L16.43246.41667L15.89917.05L12.70744.375Z" fill="#000"/>
  </svg>
);
