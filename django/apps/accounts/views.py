from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import UserCreateSerializer


class RegisterAPIView(APIView):

    serializer_class = UserCreateSerializer

    def post(self, request):
        """Registers a new user."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': "success"}, status=201)
        return Response(serializer.errors, status=400)
