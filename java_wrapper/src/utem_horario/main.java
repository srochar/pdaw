package utem_horario;

import java.io.BufferedReader;
import java.io.IOException;

public class main {
	public static void main(String[] args) {
		String user = null;
		String pass = null;

		BufferedReader reader = new BufferedReader(null);

		System.out.println("usuario:");
		try {
			user = reader.readLine();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		System.out.println("contraseña:");
		try {
			pass = reader.readLine();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		Dirdoc dirdoc = new Dirdoc(user, pass);
	}
}
