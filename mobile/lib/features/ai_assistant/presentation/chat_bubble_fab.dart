// mobile/lib/features/ai_assistant/presentation/chat_bubble_fab.dart
//
// CU18/CU19: globo de chat flotante del asistente virtual. Se coloca solo en
// el catálogo del cliente (no en el menú ni en las demás pestañas).
import 'package:flutter/material.dart';
import '../../../shared/theme/app_colors.dart';
import 'chatbot_screen.dart';

class ChatBubbleFab extends StatelessWidget {
  const ChatBubbleFab({super.key});

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      heroTag: 'asistente_chat_fab',
      backgroundColor: AppColors.bgDeep,
      foregroundColor: AppColors.primary,
      tooltip: 'Asistente SmartLook',
      onPressed: () => ChatbotSheet.mostrar(context),
      child: const Icon(Icons.chat_bubble_outline),
    );
  }
}